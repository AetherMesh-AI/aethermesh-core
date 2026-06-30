"""JSON-backed local message log persistence for batch simulations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aethermesh_core.json_io import atomic_write_json
from aethermesh_core.messages import MeshMessage, message_from_mapping
from aethermesh_core.models import Job
from aethermesh_core.scheduler import JobAssignment, ScheduledNode
from aethermesh_core.simulation import LocalSimulationResult


class MessageLogPersistenceError(ValueError):
    """Raised when a local message log JSON file cannot be safely loaded or saved."""


def build_message_log_document(
    *,
    simulation: LocalSimulationResult,
    jobs: list[Job],
    manifest_path: str | Path,
) -> dict[str, Any]:
    """Build a deterministic version 1 audit document for local mesh messages."""

    return {
        "version": 1,
        "metadata": {
            "source": "run-local-batch",
            "manifest_path": str(manifest_path),
            "message_count": len(simulation.messages),
            "node_count": len(simulation.nodes),
            "job_count": len(jobs),
            "completed_count": int(simulation.totals["completed_jobs"]),
            "failed_count": int(simulation.totals["failed_jobs"]),
            "total_contribution_units": int(simulation.totals["contribution_units"]),
            "validation_summary": dict(simulation.validation_summary),
            "node_ids": list(simulation.nodes),
            "job_ids": [job.job_id for job in jobs],
        },
        "messages": [
            _message_to_document_entry(message) for message in simulation.messages
        ],
    }


def build_replayed_message_log_document(
    *,
    replayed_messages: list[MeshMessage],
    emitted_messages: list[MeshMessage],
    node_id: str,
    source_message_log_path: str | Path,
    ledger_path: str | Path | None = None,
    processed_assignment_count: int = 0,
    ignored_message_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build a version 1 local message log for replayed plus emitted messages."""

    ignored_ids = list(ignored_message_ids or [])
    messages = [*replayed_messages, *emitted_messages]
    metadata: dict[str, Any] = {
        "source": "process-local-inbox",
        "node_id": node_id,
        "source_message_log_path": str(source_message_log_path),
        "message_count": len(messages),
        "replayed_message_count": len(replayed_messages),
        "emitted_message_count": len(emitted_messages),
        "processed_assignment_count": processed_assignment_count,
        "ignored_message_count": len(ignored_ids),
        "ignored_message_ids": ignored_ids,
    }
    if ledger_path is not None:
        metadata["ledger_path"] = str(ledger_path)

    return {
        "version": 1,
        "metadata": metadata,
        "messages": [_message_to_document_entry(message) for message in messages],
    }


def build_dispatch_message_log_document(
    *,
    messages: list[MeshMessage],
    jobs: list[Job],
    nodes: list[ScheduledNode],
    assignments: list[JobAssignment],
    manifest_path: str | Path,
) -> dict[str, Any]:
    """Build a deterministic version 1 assignment-only dispatch document."""

    return {
        "version": 1,
        "metadata": {
            "source": "dispatch-local-batch",
            "manifest_path": str(manifest_path),
            "message_count": len(messages),
            "node_count": len(nodes),
            "job_count": len(jobs),
            "assignment_count": len(assignments),
            "node_ids": [node.node_id for node in nodes],
            "job_ids": [job.job_id for job in jobs],
            "assigned_node_ids": sorted(
                {assignment.node_id for assignment in assignments}
            ),
        },
        "messages": [_message_to_document_entry(message) for message in messages],
    }


def build_flow_message_log_document(
    *,
    dispatch_messages: list[MeshMessage],
    emitted_messages_by_node: dict[str, list[MeshMessage]],
    manifest_path: str | Path,
    dispatch_message_log_path: str | Path,
    ledger_path: str | Path,
    worker_message_log_paths: dict[str, str | Path],
    available_node_ids: list[str],
    offline_node_ids: list[str],
    processed_node_ids: list[str],
    processed_assignment_count: int,
    skipped_processed_assignment_count: int,
    total_contribution_units: int,
) -> dict[str, Any]:
    """Build a deterministic version 1 run-level local flow message log."""

    emitted_messages = [
        message
        for node_id in available_node_ids
        for message in emitted_messages_by_node.get(node_id, [])
    ]
    messages = [*dispatch_messages, *emitted_messages]
    return {
        "version": 1,
        "metadata": {
            "source": "run-local-flow",
            "manifest_path": str(manifest_path),
            "dispatch_message_log_path": str(dispatch_message_log_path),
            "ledger_path": str(ledger_path),
            "worker_message_log_paths": {
                node_id: str(worker_message_log_paths[node_id])
                for node_id in available_node_ids
                if node_id in worker_message_log_paths
            },
            "available_node_ids": list(available_node_ids),
            "offline_node_ids": list(offline_node_ids),
            "processed_node_ids": list(processed_node_ids),
            "processed_assignment_count": processed_assignment_count,
            "skipped_processed_assignment_count": skipped_processed_assignment_count,
            "total_contribution_units": total_contribution_units,
            "dispatch_message_count": len(dispatch_messages),
            "emitted_message_count": len(emitted_messages),
            "message_count": len(messages),
        },
        "messages": [_message_to_document_entry(message) for message in messages],
    }


def load_message_log_messages(path: str | Path) -> list[MeshMessage]:
    """Load validated MeshMessage entries from a version 1 local message log.

    The source file is read-only: this helper never rewrites, appends, truncates,
    or normalizes the message log document it loads.
    """

    document = _load_message_log_document(path)
    messages: list[MeshMessage] = []
    for index, entry in enumerate(document["messages"]):
        messages.append(_message_from_document_entry(entry, index))
    return messages


def load_worker_emitted_messages(path: str | Path) -> list[MeshMessage]:
    """Load only post-replay worker-emitted messages from a worker message log."""

    document = _load_message_log_document(path)
    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        raise MessageLogPersistenceError(
            "message log JSON field 'metadata' must be an object"
        )
    replayed_message_count = metadata.get("replayed_message_count")
    if not isinstance(replayed_message_count, int) or replayed_message_count < 0:
        raise MessageLogPersistenceError(
            "message log metadata field 'replayed_message_count' must be a non-negative integer"
        )
    entries = document["messages"]
    if replayed_message_count > len(entries):
        raise MessageLogPersistenceError(
            "message log metadata field 'replayed_message_count' exceeds message count"
        )

    emitted: list[MeshMessage] = []
    for index, entry in enumerate(
        entries[replayed_message_count:], replayed_message_count
    ):
        message = _message_from_document_entry(entry, index)
        if message.message_type not in {"job_result_reported", "contribution_recorded"}:
            raise MessageLogPersistenceError(
                "worker emitted message log entries must be job_result_reported or contribution_recorded"
            )
        emitted.append(message)
    return emitted


def write_message_log(path: str | Path, document: dict[str, Any]) -> None:
    """Write a local message log via temp-file then atomic replace."""

    log_path = Path(path)
    try:
        atomic_write_json(log_path, document)
    except (OSError, TypeError, ValueError) as exc:
        raise MessageLogPersistenceError(
            f"could not write message log file: {exc}"
        ) from exc


def _load_message_log_document(path: str | Path) -> dict[str, Any]:
    log_path = Path(path)
    if not log_path.exists():
        raise MessageLogPersistenceError(f"message log file does not exist: {log_path}")

    try:
        with log_path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        raise MessageLogPersistenceError(
            f"message log JSON is malformed: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise MessageLogPersistenceError(
            f"could not read message log file: {exc}"
        ) from exc

    if not isinstance(document, dict):
        raise MessageLogPersistenceError("message log JSON must be an object")
    version = document.get("version")
    if version != 1 or isinstance(version, bool):
        raise MessageLogPersistenceError("message log JSON must contain version 1")
    entries = document.get("messages")
    if not isinstance(entries, list):
        raise MessageLogPersistenceError(
            "message log JSON field 'messages' must be a list"
        )
    return document


def _message_to_document_entry(message: MeshMessage) -> dict[str, Any]:
    return {
        "message_id": message.message_id,
        "message_type": message.message_type,
        "sender_node_id": message.sender_node_id,
        "recipient_node_id": message.recipient_node_id,
        "payload": dict(message.payload),
        "correlation_id": message.correlation_id,
    }


def _message_from_document_entry(entry: Any, index: int) -> MeshMessage:
    try:
        return message_from_mapping(entry)
    except ValueError as exc:
        raise MessageLogPersistenceError(
            f"message log entry {index} is invalid: {exc}"
        ) from exc
