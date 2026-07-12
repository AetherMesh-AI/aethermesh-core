"""Validation for local, evidence-backed job-failure records."""

from __future__ import annotations

from datetime import datetime
from pathlib import PurePosixPath
from typing import Any

JOB_FAILURE_SCHEMA_VERSION = 1
FAILURE_TYPES = frozenset(
    {
        "task_crash",
        "validation_failure",
        "timeout",
        "manifest_mismatch",
        "contribution_rejected",
    }
)
FAILURE_STAGES = frozenset(
    {"input", "execution", "output", "validation", "attribution"}
)
SEVERITIES = frozenset({"info", "warning", "error", "critical"})
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
        "links",
        "attribution",
        "evidence",
    }
)
_DETAIL_FIELDS = frozenset(
    {
        "exit_code",
        "signal",
        "timeout_ms",
        "validation_error",
        "missing_input",
        "manifest_mismatch",
        "receipt_mismatch",
        "environment_issue",
    }
)
_LINK_FIELDS = frozenset(
    {
        "job_manifest_hash",
        "input_manifest_hash",
        "output_manifest_hash",
        "validation_receipt_ids",
        "lineage_parent_ids",
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
    {"local_log_paths", "content_hashes", "validation_command_refs", "observed_at"}
)


class JobFailureSchemaError(ValueError):
    """Raised when a job-failure record violates the versioned contract."""


def validate_job_failure_document(document: object) -> dict[str, Any]:
    """Validate a failure record without reading logs or dereferencing evidence."""

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
    _choice(failure["failure_type"], FAILURE_TYPES, "failure_type")
    _choice(failure["failure_stage"], FAILURE_STAGES, "failure_stage")
    _choice(failure["severity"], SEVERITIES, "severity")
    if not isinstance(failure["retryable"], bool):
        raise JobFailureSchemaError("job failure.retryable must be boolean")
    _bounded_text(failure["human_summary"], "job failure.human_summary")
    _details(failure["details"])
    _links(failure["links"])
    _attribution(failure["attribution"])
    _evidence(failure["evidence"])
    return failure


def _object(value: object, context: str, fields: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise JobFailureSchemaError(f"{context} must be an object")
    missing, unknown = sorted(fields - set(value)), sorted(set(value) - fields)
    if missing or unknown:
        parts = ([f"missing: {', '.join(missing)}"] if missing else []) + (
            [f"unsupported: {', '.join(unknown)}"] if unknown else []
        )
        raise JobFailureSchemaError(f"{context} fields invalid ({'; '.join(parts)})")
    return value


def _identifier(value: object, context: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(c.isspace() for c in value)
    ):
        raise JobFailureSchemaError(f"{context} must be a non-empty identifier")
    return value


def _timestamp(value: object, context: str) -> None:
    if not isinstance(value, str):
        raise JobFailureSchemaError(f"{context} must be a UTC timestamp")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise JobFailureSchemaError(f"{context} must be a UTC timestamp") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z" != value:
        raise JobFailureSchemaError(f"{context} must have millisecond precision")


def _choice(value: object, choices: frozenset[str], field: str) -> None:
    if value not in choices:
        raise JobFailureSchemaError(f"job failure.{field} is unsupported")


def _bounded_text(value: object, context: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise JobFailureSchemaError(
            f"{context} must be a non-empty string up to 512 characters"
        )


def _nullable_text(value: object, context: str) -> None:
    if value is not None:
        _bounded_text(value, context)


def _details(value: object) -> None:
    details = _object(value, "job failure.details", _DETAIL_FIELDS)
    for field in ("exit_code", "signal", "timeout_ms"):
        item = details[field]
        if item is not None and (
            not isinstance(item, int) or isinstance(item, bool) or item < 0
        ):
            raise JobFailureSchemaError(
                f"job failure.details.{field} must be a non-negative integer or null"
            )
    for field in _DETAIL_FIELDS - {"exit_code", "signal", "timeout_ms"}:
        _nullable_text(details[field], f"job failure.details.{field}")
    if all(item is None for item in details.values()):
        raise JobFailureSchemaError(
            "job failure.details must describe at least one failure observation"
        )


def _links(value: object) -> None:
    links = _object(value, "job failure.links", _LINK_FIELDS)
    for field in ("job_manifest_hash", "input_manifest_hash"):
        _identifier(links[field], f"job failure.links.{field}")
    if links["output_manifest_hash"] is not None:
        _identifier(
            links["output_manifest_hash"], "job failure.links.output_manifest_hash"
        )
    for field in ("validation_receipt_ids", "lineage_parent_ids"):
        _identifier_list(links[field], f"job failure.links.{field}")


def _attribution(value: object) -> None:
    attribution = _object(value, "job failure.attribution", _ATTRIBUTION_FIELDS)
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
    _nullable_text(
        attribution["rejection_reason"], "job failure.attribution.rejection_reason"
    )
    if amount == 0 and attribution["rejection_reason"] is None:
        raise JobFailureSchemaError(
            "rejected contribution must include rejection_reason"
        )


def _evidence(value: object) -> None:
    evidence = _object(value, "job failure.evidence", _EVIDENCE_FIELDS)
    paths = evidence["local_log_paths"]
    if not isinstance(paths, list):
        raise JobFailureSchemaError(
            "job failure.evidence.local_log_paths must be a list"
        )
    for path in paths:
        _identifier(path, "job failure.evidence.local_log_paths entries")
        parsed = PurePosixPath(path)
        if parsed.is_absolute() or ".." in parsed.parts:
            raise JobFailureSchemaError(
                "local log paths must be safe repository-relative references"
            )
    for field in ("content_hashes", "validation_command_refs"):
        _identifier_list(evidence[field], f"job failure.evidence.{field}")
    timestamps = evidence["observed_at"]
    if not isinstance(timestamps, list) or not timestamps:
        raise JobFailureSchemaError(
            "job failure.evidence.observed_at must be a non-empty list"
        )
    for timestamp in timestamps:
        _timestamp(timestamp, "job failure.evidence.observed_at entries")
    if (
        not paths
        and not evidence["content_hashes"]
        and not evidence["validation_command_refs"]
    ):
        raise JobFailureSchemaError(
            "job failure.evidence must include an evidence reference"
        )


def _identifier_list(value: object, context: str) -> None:
    if not isinstance(value, list):
        raise JobFailureSchemaError(f"{context} must be a list")
    for item in value:
        _identifier(item, f"{context} entries")
