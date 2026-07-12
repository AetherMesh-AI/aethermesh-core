"""Validation for local, auditable Phase 1 job-result records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

JOB_RESULT_SCHEMA_VERSION = 1
RESULT_STATUSES = frozenset({"succeeded", "failed"})
VALIDATION_STATUSES = frozenset({"passed", "failed", "error", "not_run"})
_FAILURE_FIELDS = frozenset(
    {"execution", "validation", "malformed_input", "missing_artifact"}
)
_LINEAGE_FIELDS = frozenset(
    {
        "input_manifest_ids",
        "output_manifest_ids",
        "parent_job_ids",
        "parent_task_ids",
        "artifact_ids",
    }
)
_CONTRIBUTION_FIELDS = frozenset({"attribution_node_id", "local_operator_id"})
_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "result_id",
        "job_id",
        "task_id",
        "creator_node_id",
        "executor_node_id",
        "manifest_id",
        "created_at",
        "status",
        "exit_code",
        "started_at",
        "finished_at",
        "duration_ms",
        "summary",
        "validation_status",
        "validation_receipt_id",
        "validator_node_id",
        "failure_reasons",
        "lineage",
        "contribution",
    }
)


class JobResultSchemaError(ValueError):
    """Raised when a local job-result record violates its stable schema."""


def validate_job_result_document(document: object) -> dict[str, Any]:
    """Validate one local-only result record without reading or writing files."""

    result = _object(document, "job result", _REQUIRED_FIELDS)
    _exact_integer(result["schema_version"], "job result.schema_version", 1)
    for field in (
        "result_id",
        "job_id",
        "task_id",
        "creator_node_id",
        "executor_node_id",
        "manifest_id",
        "validation_receipt_id",
        "validator_node_id",
    ):
        _identifier(result[field], f"job result.{field}")
    created_at = _timestamp(result["created_at"], "job result.created_at")
    started_at = _timestamp(result["started_at"], "job result.started_at")
    finished_at = _timestamp(result["finished_at"], "job result.finished_at")
    if created_at > started_at or finished_at < started_at:
        raise JobResultSchemaError(
            "job result timestamps must be chronologically ordered"
        )
    duration_ms = result["duration_ms"]
    if (
        not isinstance(duration_ms, int)
        or isinstance(duration_ms, bool)
        or duration_ms < 0
    ):
        raise JobResultSchemaError(
            "job result.duration_ms must be a non-negative integer"
        )
    if duration_ms != int((finished_at - started_at).total_seconds() * 1000):
        raise JobResultSchemaError(
            "job result.duration_ms must match started_at and finished_at"
        )
    if result["status"] not in RESULT_STATUSES:
        raise JobResultSchemaError("job result.status must be succeeded or failed")
    exit_code = result["exit_code"]
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise JobResultSchemaError("job result.exit_code must be an integer")
    summary = result["summary"]
    if not isinstance(summary, str) or not summary or len(summary) > 512:
        raise JobResultSchemaError(
            "job result.summary must be a non-empty string up to 512 characters"
        )
    if result["validation_status"] not in VALIDATION_STATUSES:
        raise JobResultSchemaError(
            "job result.validation_status must be passed, failed, error, or not_run"
        )
    _failure_reasons(result["failure_reasons"])
    _lineage(result["lineage"])
    _contribution(result["contribution"], result["executor_node_id"])
    return result


def _object(value: object, context: str, required: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise JobResultSchemaError(f"{context} must be an object")
    fields = set(value)
    missing = sorted(required - fields)
    unknown = sorted(fields - required)
    if missing or unknown:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if unknown:
            details.append(f"unsupported: {', '.join(unknown)}")
        raise JobResultSchemaError(f"{context} fields invalid ({'; '.join(details)})")
    return value


def _identifier(value: object, context: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(character.isspace() for character in value)
    ):
        raise JobResultSchemaError(f"{context} must be a non-empty identifier")
    return value


def _timestamp(value: object, context: str) -> datetime:
    if not isinstance(value, str):
        raise JobResultSchemaError(f"{context} must be a UTC timestamp")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise JobResultSchemaError(f"{context} must be a UTC timestamp") from exc
    return parsed


def _exact_integer(value: object, context: str, expected: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value != expected:
        raise JobResultSchemaError(f"{context} must be integer {expected}")


def _failure_reasons(value: object) -> None:
    reasons = _object(value, "job result.failure_reasons", _FAILURE_FIELDS)
    for field, reason in reasons.items():
        if reason is not None and (not isinstance(reason, str) or not reason):
            raise JobResultSchemaError(
                f"job result.failure_reasons.{field} must be a non-empty string or null"
            )


def _lineage(value: object) -> None:
    lineage = _object(value, "job result.lineage", _LINEAGE_FIELDS)
    for field, references in lineage.items():
        if not isinstance(references, list):
            raise JobResultSchemaError(f"job result.lineage.{field} must be a list")
        for reference in references:
            _identifier(reference, f"job result.lineage.{field} entries")


def _contribution(value: object, executor_node_id: object) -> None:
    contribution = _object(value, "job result.contribution", _CONTRIBUTION_FIELDS)
    if contribution["attribution_node_id"] != executor_node_id:
        raise JobResultSchemaError(
            "job result.contribution.attribution_node_id must match executor_node_id"
        )
    _identifier(
        contribution["attribution_node_id"],
        "job result.contribution.attribution_node_id",
    )
    operator = contribution["local_operator_id"]
    if operator is not None:
        _identifier(operator, "job result.contribution.local_operator_id")
