"""Local-only collection of worker result message logs."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aethermesh_core.message_log import load_message_log_messages
from aethermesh_core.messages import MeshMessage


class ResultCollectionError(ValueError):
    """Raised when local worker result logs cannot be reconciled safely."""


@dataclass(frozen=True)
class _KnownAssignment:
    key: str
    job_id: str
    node_id: str


def collect_local_results(
    *,
    dispatch_message_log_path: str | Path,
    worker_message_log_paths: list[str | Path],
) -> dict[str, object]:
    """Validate and summarize worker output logs for one local dispatch log.

    Input logs are read-only. This collector reconciles ``job_result_reported``
    and ``contribution_recorded`` messages emitted by workers against the
    ``job_assigned`` messages in the dispatch log.
    """

    if not worker_message_log_paths:
        raise ResultCollectionError("at least one worker message log path is required")

    dispatch_messages = load_message_log_messages(dispatch_message_log_path)
    assignments = _known_assignments(dispatch_messages)

    collected_messages: list[MeshMessage] = []
    duplicate_message_ids: list[str] = []
    conflicting_message_ids: list[str] = []
    seen_by_message_id: dict[str, dict[str, Any]] = {}
    seen_by_worker_message_id: dict[tuple[str, str], dict[str, Any]] = {}
    result_keys: set[str] = set()
    contribution_count = 0
    per_node_units: dict[str, int] = defaultdict(int)

    for worker_path in worker_message_log_paths:
        worker_path_key = str(worker_path)
        for message in load_message_log_messages(worker_path):
            if message.message_type not in {
                "job_result_reported",
                "contribution_recorded",
            }:
                continue

            message_dict = message.to_dict()
            worker_message_key = (worker_path_key, message.message_id)
            existing_worker_message = seen_by_worker_message_id.get(worker_message_key)
            if existing_worker_message is not None:
                if existing_worker_message != message_dict:
                    _append_once(conflicting_message_ids, message.message_id)
                    continue
                _append_once(duplicate_message_ids, message.message_id)
                continue
            seen_by_worker_message_id[worker_message_key] = message_dict

            existing_message = seen_by_message_id.get(message.message_id)
            if existing_message == message_dict:
                _append_once(duplicate_message_ids, message.message_id)
                continue
            if existing_message is None:
                seen_by_message_id[message.message_id] = message_dict

            key = _result_or_contribution_key(message)
            assignment = assignments.get(key)
            if assignment is None:
                raise ResultCollectionError(
                    f"{message.message_type} message {message.message_id} references unknown assignment: {key}"
                )
            payload_job_id = message.payload.get("job_id")
            if payload_job_id != assignment.job_id:
                raise ResultCollectionError(
                    f"{message.message_type} message {message.message_id} job_id {payload_job_id!r} does not match assignment job_id {assignment.job_id!r}"
                )
            if message.message_type == "job_result_reported":
                _validate_result_reporter(message, assignment)

            collected_messages.append(message)
            if message.message_type == "job_result_reported":
                result_keys.add(key)
            else:
                contribution_count += 1
                node_id = message.payload.get("node_id")
                contribution_units = message.payload.get("contribution_units")
                if not isinstance(node_id, str) or node_id == "":
                    raise ResultCollectionError(
                        f"contribution_recorded message {message.message_id} payload.node_id must be a non-empty string"
                    )
                if not isinstance(contribution_units, int) or isinstance(
                    contribution_units, bool
                ):
                    raise ResultCollectionError(
                        f"contribution_recorded message {message.message_id} payload.contribution_units must be an integer"
                    )
                _validate_contribution_recipient(message, assignment, node_id)
                per_node_units[node_id] += contribution_units

    if conflicting_message_ids:
        joined = ", ".join(conflicting_message_ids)
        raise ResultCollectionError(f"conflicting duplicate message_id values: {joined}")

    missing_assignment_ids = [key for key in assignments if key not in result_keys]
    return {
        "command": "collect-local-results",
        "dispatch_message_log_path": str(dispatch_message_log_path),
        "worker_message_log_paths": [str(path) for path in worker_message_log_paths],
        "known_assignment_count": len(assignments),
        "reported_result_count": sum(
            1 for message in collected_messages if message.message_type == "job_result_reported"
        ),
        "contribution_recorded_count": contribution_count,
        "missing_assignment_ids": missing_assignment_ids,
        "duplicate_message_ids": duplicate_message_ids,
        "conflicting_message_ids": [],
        "per_node_contribution_units": dict(sorted(per_node_units.items())),
        "total_contribution_units": sum(per_node_units.values()),
        "collected_message_ids": [message.message_id for message in collected_messages],
    }


def _known_assignments(messages: list[MeshMessage]) -> dict[str, _KnownAssignment]:
    assignments: dict[str, _KnownAssignment] = {}
    for message in messages:
        if message.message_type != "job_assigned":
            continue
        key = _assignment_key(message)
        job_id = message.payload.get("job_id")
        if not isinstance(job_id, str) or job_id == "":
            raise ResultCollectionError(
                f"job_assigned message {message.message_id} payload.job_id must be a non-empty string"
            )
        if not isinstance(message.recipient_node_id, str) or message.recipient_node_id == "":
            raise ResultCollectionError(
                f"job_assigned message {message.message_id} recipient_node_id must be a non-empty string"
            )
        existing = assignments.get(key)
        assignment = _KnownAssignment(
            key=key,
            job_id=job_id,
            node_id=message.recipient_node_id,
        )
        if existing is not None and existing != assignment:
            raise ResultCollectionError(
                f"assignment key {key!r} maps to multiple assignment values"
            )
        assignments[key] = assignment
    return assignments


def _validate_result_reporter(
    message: MeshMessage, assignment: _KnownAssignment
) -> None:
    if message.sender_node_id != assignment.node_id:
        raise ResultCollectionError(
            f"job_result_reported message {message.message_id} sender_node_id {message.sender_node_id!r} does not match assigned node_id {assignment.node_id!r}"
        )


def _validate_contribution_recipient(
    message: MeshMessage, assignment: _KnownAssignment, node_id: str
) -> None:
    if node_id != assignment.node_id:
        raise ResultCollectionError(
            f"contribution_recorded message {message.message_id} payload.node_id {node_id!r} does not match assigned node_id {assignment.node_id!r}"
        )
    if message.recipient_node_id != assignment.node_id:
        raise ResultCollectionError(
            f"contribution_recorded message {message.message_id} recipient_node_id {message.recipient_node_id!r} does not match assigned node_id {assignment.node_id!r}"
        )


def _assignment_key(message: MeshMessage) -> str:
    if message.correlation_id is not None:
        return message.correlation_id
    payload_job_id = message.payload.get("job_id")
    if isinstance(payload_job_id, str) and payload_job_id != "":
        return payload_job_id
    raise ResultCollectionError(
        f"job_assigned message {message.message_id} must include correlation_id or payload.job_id"
    )


def _result_or_contribution_key(message: MeshMessage) -> str:
    payload_job_id = message.payload.get("job_id")
    if not isinstance(payload_job_id, str) or payload_job_id == "":
        raise ResultCollectionError(
            f"{message.message_type} message {message.message_id} payload.job_id must be a non-empty string"
        )
    if message.correlation_id is not None and message.correlation_id != payload_job_id:
        raise ResultCollectionError(
            f"{message.message_type} message {message.message_id} correlation_id and payload.job_id disagree"
        )
    return message.correlation_id or payload_job_id


def _append_once(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
