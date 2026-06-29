"""JSON-backed local message log persistence for batch simulations."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job
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
        "messages": [_message_to_document_entry(message) for message in simulation.messages],
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


def load_message_log_messages(path: str | Path) -> list[MeshMessage]:
    """Load validated MeshMessage entries from a version 1 local message log.

    The source file is read-only: this helper never rewrites, appends, truncates,
    or normalizes the message log document it loads.
    """

    log_path = Path(path)
    if not log_path.exists():
        raise MessageLogPersistenceError(f"message log file does not exist: {log_path}")

    try:
        with log_path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        raise MessageLogPersistenceError(f"message log JSON is malformed: {exc.msg}") from exc
    except OSError as exc:
        raise MessageLogPersistenceError(f"could not read message log file: {exc}") from exc

    if not isinstance(document, dict):
        raise MessageLogPersistenceError("message log JSON must be an object")
    if document.get("version") != 1:
        raise MessageLogPersistenceError("message log JSON must contain version 1")
    entries = document.get("messages")
    if not isinstance(entries, list):
        raise MessageLogPersistenceError("message log JSON field 'messages' must be a list")

    messages: list[MeshMessage] = []
    for index, entry in enumerate(entries):
        messages.append(_message_from_document_entry(entry, index))
    return messages


def write_message_log(path: str | Path, document: dict[str, Any]) -> None:
    """Write a local message log via temp-file then atomic replace."""

    log_path = Path(path)
    parent = log_path.parent
    temp_name: str | None = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=parent,
            prefix=f".{log_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, log_path)
    except (OSError, TypeError, ValueError) as exc:
        if temp_name is not None:
            _remove_temp_file(temp_name)
        raise MessageLogPersistenceError(f"could not write message log file: {exc}") from exc


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
    if not isinstance(entry, dict):
        raise MessageLogPersistenceError(
            f"message log entry {index} must be an object"
        )
    message_id = entry.get("message_id")
    message_type = entry.get("message_type")
    sender_node_id = entry.get("sender_node_id")
    recipient_node_id = entry.get("recipient_node_id")
    payload = entry.get("payload", {})
    correlation_id = entry.get("correlation_id")
    try:
        if not isinstance(message_id, str):
            raise ValueError("message_id must be a non-empty string")
        if not isinstance(message_type, str):
            raise ValueError("message_type must be a non-empty string")
        if not isinstance(sender_node_id, str):
            raise ValueError("sender_node_id must be a non-empty string")
        return MeshMessage(
            message_id=message_id,
            message_type=message_type,
            sender_node_id=sender_node_id,
            recipient_node_id=recipient_node_id,
            payload=payload,
            correlation_id=correlation_id,
        )
    except ValueError as exc:
        raise MessageLogPersistenceError(
            f"message log entry {index} is invalid: {exc}"
        ) from exc


def _remove_temp_file(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        return
