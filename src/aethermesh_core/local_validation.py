"""Independent local replay validation for reported AetherMesh job results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethermesh_core.json_io import atomic_write_json
from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    load_message_log_messages,
)
from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job, JobResult
from aethermesh_core.validation import validate_job_result


class LocalValidationError(ValueError):
    """Raised when local validation replay cannot safely produce an artifact."""


AssignmentKey = tuple[str | None, str]


def validate_local_results(
    *,
    assignment_log_path: str | Path,
    result_log_path: str | Path,
    validation_log_path: str | Path,
) -> dict[str, Any]:
    """Replay assignment/result logs and write an independent validation report."""

    output_path = Path(validation_log_path)
    if output_path.exists():
        raise LocalValidationError(f"validation output already exists: {output_path}")

    try:
        assignment_log_messages = load_message_log_messages(assignment_log_path)
        result_log_messages = load_message_log_messages(result_log_path)
    except MessageLogPersistenceError as exc:
        raise LocalValidationError(str(exc)) from exc

    assignments = [
        message
        for message in assignment_log_messages
        if message.message_type == "job_assigned"
    ]
    results = [
        message
        for message in result_log_messages
        if message.message_type == "job_result_reported"
    ]

    jobs_by_key: dict[AssignmentKey, Job] = {}
    assignment_message_ids_by_key: dict[AssignmentKey, str] = {}
    for assignment in assignments:
        job = _job_from_assignment(assignment)
        key = _assignment_key(assignment.correlation_id, job.job_id)
        if key in jobs_by_key:
            raise LocalValidationError(
                "multiple job_assigned messages share validation key "
                f"correlation_id={key[0]!r} job_id={key[1]!r}"
            )
        jobs_by_key[key] = job
        assignment_message_ids_by_key[key] = assignment.message_id

    result_messages_by_key: dict[AssignmentKey, MeshMessage] = {}
    for result_message in results:
        result = _result_from_message(result_message)
        key = _assignment_key(result_message.correlation_id, result.job_id)
        if key in result_messages_by_key:
            raise LocalValidationError(
                "multiple job_result_reported messages share validation key "
                f"correlation_id={key[0]!r} job_id={key[1]!r}"
            )
        result_messages_by_key[key] = result_message

    validations: list[dict[str, Any]] = []
    for key in sorted(result_messages_by_key, key=_sort_key):
        result_message = result_messages_by_key[key]
        assigned_job = jobs_by_key.get(key)
        if assigned_job is None:
            raise LocalValidationError(
                "job_result_reported has no matching job_assigned message "
                f"correlation_id={key[0]!r} job_id={key[1]!r}"
            )
        result = _result_from_message(result_message)
        validation = validate_job_result(assigned_job, result)
        validations.append(
            {
                "message_type": "job_result_validated",
                "assignment_message_id": assignment_message_ids_by_key[key],
                "result_message_id": result_message.message_id,
                "job_id": assigned_job.job_id,
                "correlation_id": result_message.correlation_id,
                "result_sender": result_message.sender_node_id,
                "valid": validation.valid,
                "reason": validation.reason,
            }
        )

    valid_count = sum(1 for entry in validations if bool(entry["valid"]))
    document: dict[str, Any] = {
        "version": 1,
        "kind": "local_validation_report",
        "summary": {
            "assignments_seen": len(assignments),
            "results_seen": len(results),
            "results_validated": len(validations),
            "valid_results": valid_count,
            "invalid_results": len(validations) - valid_count,
        },
        "validations": validations,
    }
    try:
        atomic_write_json(output_path, document)
    except (OSError, TypeError, ValueError) as exc:
        raise LocalValidationError(
            f"could not write validation report file: {exc}"
        ) from exc
    return document


def _assignment_key(correlation_id: str | None, job_id: str) -> AssignmentKey:
    return (correlation_id, job_id)


def _sort_key(key: AssignmentKey) -> tuple[str, str]:
    correlation_id, job_id = key
    return ("" if correlation_id is None else correlation_id, job_id)


def _job_from_assignment(message: MeshMessage) -> Job:
    payload = message.payload
    job_id = _required_non_empty_string(payload, "job_id", "job_assigned")
    job_type = _required_non_empty_string(payload, "job_type", "job_assigned")
    job_payload = payload.get("payload")
    if not isinstance(job_payload, dict):
        raise LocalValidationError(
            "job_assigned payload field 'payload' must be an object"
        )
    return Job(job_id=job_id, job_type=job_type, payload=dict(job_payload))


def _result_from_message(message: MeshMessage) -> JobResult:
    payload = message.payload
    job_id = _required_non_empty_string(payload, "job_id", "job_result_reported")
    status = _required_non_empty_string(payload, "status", "job_result_reported")
    if "output" not in payload:
        raise LocalValidationError(
            "job_result_reported payload field 'output' is required"
        )
    error = payload.get("error")
    if error is not None and not isinstance(error, str):
        raise LocalValidationError(
            "job_result_reported payload field 'error' must be a string or null"
        )
    contribution_units = payload.get("contribution_units")
    if not isinstance(contribution_units, int) or isinstance(contribution_units, bool):
        raise LocalValidationError(
            "job_result_reported payload field 'contribution_units' must be an integer"
        )
    return JobResult(
        job_id=job_id,
        node_id=message.sender_node_id,
        status=status,
        output=payload["output"],
        error=error,
        contribution_units=contribution_units,
    )


def _required_non_empty_string(
    payload: dict[str, Any], field_name: str, message_type: str
) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or value == "":
        raise LocalValidationError(
            f"{message_type} payload field '{field_name}' must be a non-empty string"
        )
    return value
