"""Validation for local, evidence-backed job-failure records."""

from __future__ import annotations

from datetime import datetime
from typing import Any

JOB_FAILURE_SCHEMA_VERSION = 1
FAILURE_TYPES = frozenset(
    {
        "task_crash",
        "validation_failure",
        "timeout",
        "manifest_mismatch",
        "contribution_rejected",
        "missing_input",
        "environment_failure",
    }
)
FAILURE_STAGES = frozenset(
    {"input", "execution", "output", "validation", "attribution"}
)
SEVERITIES = frozenset({"warning", "error", "critical"})
_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "failure_id",
        "job_id",
        "task_id",
        "creator_node_id",
        "executing_node_id",
        "observed_at",
        "failure_type",
        "failure_stage",
        "retryable",
        "severity",
        "human_summary",
        "details",
        "references",
        "attribution",
        "evidence",
    }
)
_DETAIL_FIELDS = frozenset(
    {
        "exit_code",
        "signal",
        "timeout_ms",
        "validation_error_code",
        "missing_input_id",
        "manifest_mismatch",
        "receipt_mismatch",
        "environment_issue_code",
    }
)
_REFERENCE_FIELDS = frozenset(
    {
        "job_manifest_hash",
        "input_manifest_hash",
        "output_manifest_hash",
        "validation_receipt_ids",
        "lineage_parent_ids",
        "attribution_record_ids",
    }
)
_ATTRIBUTION_FIELDS = frozenset(
    {
        "attempted_contributor_node_id",
        "claimed_work_unit",
        "accepted_work_amount",
        "rejection_reason",
    }
)
_EVIDENCE_FIELDS = frozenset(
    {
        "local_log_paths",
        "content_hashes",
        "validation_command_refs",
        "observed_timestamps",
    }
)


class JobFailureSchemaError(ValueError):
    """Raised when a job-failure record violates its stable schema."""


def validate_job_failure_document(document: object) -> dict[str, Any]:
    """Validate one local failure record without persisting sensitive payloads."""

    failure = _object(document, "job failure", _REQUIRED_FIELDS)
    if failure["schema_version"] != JOB_FAILURE_SCHEMA_VERSION or isinstance(
        failure["schema_version"], bool
    ):
        raise JobFailureSchemaError("job failure.schema_version must be integer 1")
    for field in ("failure_id", "job_id", "creator_node_id", "executing_node_id"):
        _identifier(failure[field], f"job failure.{field}")
    if failure["task_id"] is not None:
        _identifier(failure["task_id"], "job failure.task_id")
    _timestamp(failure["observed_at"], "job failure.observed_at")
    _enum(failure["failure_type"], FAILURE_TYPES, "job failure.failure_type")
    _enum(failure["failure_stage"], FAILURE_STAGES, "job failure.failure_stage")
    _enum(failure["severity"], SEVERITIES, "job failure.severity")
    if not isinstance(failure["retryable"], bool):
        raise JobFailureSchemaError("job failure.retryable must be a boolean")
    summary = failure["human_summary"]
    if not isinstance(summary, str) or not summary or len(summary) > 512:
        raise JobFailureSchemaError(
            "job failure.human_summary must be a non-empty string up to 512 characters"
        )
    _details(failure["details"])
    _references(failure["references"])
    _attribution(failure["attribution"], failure["executing_node_id"])
    _evidence(failure["evidence"], failure["observed_at"])
    return failure


def _object(value: object, context: str, required: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise JobFailureSchemaError(f"{context} must be an object")
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        if unknown:
            parts.append(f"unsupported: {', '.join(unknown)}")
        raise JobFailureSchemaError(f"{context} fields invalid ({'; '.join(parts)})")
    return value


def _identifier(value: object, context: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(character.isspace() for character in value)
    ):
        raise JobFailureSchemaError(f"{context} must be a non-empty identifier")
    return value


def _timestamp(value: object, context: str) -> datetime:
    if not isinstance(value, str):
        raise JobFailureSchemaError(f"{context} must be a UTC timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise JobFailureSchemaError(f"{context} must be a UTC timestamp") from exc


def _enum(value: object, choices: frozenset[str], context: str) -> None:
    if value not in choices:
        raise JobFailureSchemaError(f"{context} is unsupported")


def _nullable_identifier(value: object, context: str) -> None:
    if value is not None:
        _identifier(value, context)


def _details(value: object) -> None:
    details = _object(value, "job failure.details", _DETAIL_FIELDS)
    for field in (
        "signal",
        "validation_error_code",
        "missing_input_id",
        "manifest_mismatch",
        "receipt_mismatch",
        "environment_issue_code",
    ):
        _nullable_identifier(details[field], f"job failure.details.{field}")
    for field in ("exit_code", "timeout_ms"):
        number = details[field]
        if number is not None and (
            not isinstance(number, int) or isinstance(number, bool) or number < 0
        ):
            raise JobFailureSchemaError(
                f"job failure.details.{field} must be a non-negative integer or null"
            )


def _references(value: object) -> None:
    references = _object(value, "job failure.references", _REFERENCE_FIELDS)
    for field in ("job_manifest_hash", "input_manifest_hash"):
        _identifier(references[field], f"job failure.references.{field}")
    _nullable_identifier(
        references["output_manifest_hash"],
        "job failure.references.output_manifest_hash",
    )
    for field in (
        "validation_receipt_ids",
        "lineage_parent_ids",
        "attribution_record_ids",
    ):
        _identifier_list(references[field], f"job failure.references.{field}")


def _attribution(value: object, executing_node_id: object) -> None:
    attribution = _object(value, "job failure.attribution", _ATTRIBUTION_FIELDS)
    if attribution["attempted_contributor_node_id"] != executing_node_id:
        raise JobFailureSchemaError(
            "job failure.attribution.attempted_contributor_node_id must match executing_node_id"
        )
    _identifier(
        attribution["attempted_contributor_node_id"],
        "job failure.attribution.attempted_contributor_node_id",
    )
    _identifier(
        attribution["claimed_work_unit"], "job failure.attribution.claimed_work_unit"
    )
    amount = attribution["accepted_work_amount"]
    if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
        raise JobFailureSchemaError(
            "job failure.attribution.accepted_work_amount must be a non-negative integer"
        )
    reason = attribution["rejection_reason"]
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise JobFailureSchemaError(
            "job failure.attribution.rejection_reason must be a non-empty string or null"
        )


def _evidence(value: object, observed_at: object) -> None:
    evidence = _object(value, "job failure.evidence", _EVIDENCE_FIELDS)
    for field in ("local_log_paths", "content_hashes", "validation_command_refs"):
        _identifier_list(evidence[field], f"job failure.evidence.{field}")
    timestamps = evidence["observed_timestamps"]
    if not isinstance(timestamps, list) or not timestamps:
        raise JobFailureSchemaError(
            "job failure.evidence.observed_timestamps must be a non-empty list"
        )
    for timestamp in timestamps:
        _timestamp(timestamp, "job failure.evidence.observed_timestamps entries")
    if not any(
        evidence[field]
        for field in ("local_log_paths", "content_hashes", "validation_command_refs")
    ):
        raise JobFailureSchemaError(
            "job failure.evidence must contain an evidence reference"
        )
    if observed_at not in timestamps:
        raise JobFailureSchemaError(
            "job failure.evidence.observed_timestamps must include observed_at"
        )


def _identifier_list(value: object, context: str) -> None:
    if not isinstance(value, list):
        raise JobFailureSchemaError(f"{context} must be a list")
    for item in value:
        _identifier(item, f"{context} entries")
