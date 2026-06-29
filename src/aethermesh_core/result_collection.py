"""Local-only collection of worker result message logs."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from aethermesh_core.message_log import load_message_log_messages
from aethermesh_core.messages import MeshMessage


class ResultCollectionError(ValueError):
    """Raised when local worker result logs cannot be reconciled safely."""


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
    result_keys: set[str] = set()
    contribution_count = 0
    per_node_units: dict[str, int] = defaultdict(int)

    for worker_path in worker_message_log_paths:
        for message in load_message_log_messages(worker_path):
            if message.message_type not in {
                "job_result_reported",
                "contribution_recorded",
            }:
                continue

            message_dict = message.to_dict()
            existing = seen_by_message_id.get(message.message_id)
            if existing is not None:
                if existing != message_dict:
                    _append_once(conflicting_message_ids, message.message_id)
                    continue
                _append_once(duplicate_message_ids, message.message_id)
                continue
            seen_by_message_id[message.message_id] = message_dict

            key = _result_or_contribution_key(message)
            assignment_job_id = assignments.get(key)
            if assignment_job_id is None:
                raise ResultCollectionError(
                    f"{message.message_type} message {message.message_id} references unknown assignment: {key}"
                )
            payload_job_id = message.payload.get("job_id")
            if payload_job_id != assignment_job_id:
                raise ResultCollectionError(
                    f"{message.message_type} message {message.message_id} job_id {payload_job_id!r} does not match assignment job_id {assignment_job_id!r}"
                )

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


def _known_assignments(messages: list[MeshMessage]) -> dict[str, str]:
    assignments: dict[str, str] = {}
    for message in messages:
        if message.message_type != "job_assigned":
            continue
        key = _assignment_key(message)
        job_id = message.payload.get("job_id")
        if not isinstance(job_id, str) or job_id == "":
            raise ResultCollectionError(
                f"job_assigned message {message.message_id} payload.job_id must be a non-empty string"
            )
        existing = assignments.get(key)
        if existing is not None and existing != job_id:
            raise ResultCollectionError(
                f"assignment key {key!r} maps to multiple job_id values"
            )
        assignments[key] = job_id
    return assignments


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
