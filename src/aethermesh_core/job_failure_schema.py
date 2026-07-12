"""Validation for local, attributable Phase 1 job-failure records."""

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
        "rejected_contribution",
        "missing_input",
        "receipt_mismatch",
        "execution_environment",
    }
)
FAILURE_STAGES = frozenset({"input", "execution", "validation", "attribution"})
SEVERITIES = frozenset({"info", "warning", "error", "critical"})
_REQUIRED = frozenset(
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
_DETAILS = frozenset(
    {
        "exit_code",
        "signal",
        "timeout_ms",
        "validation_error_code",
        "missing_input_id",
        "expected_manifest_hash",
        "observed_manifest_hash",
        "expected_receipt_id",
        "observed_receipt_id",
        "environment_issue_code",
    }
)
_LINKS = frozenset(
    {
        "job_manifest_hash",
        "input_manifest_hash",
        "output_manifest_hash",
        "validation_receipt_ids",
        "lineage_parent_ids",
        "attribution_record_ids",
    }
)
_ATTRIBUTION = frozenset(
    {
        "attempted_contributor_node_id",
        "claimed_work_unit",
        "accepted_work_amount",
        "rejection_reason",
    }
)
_EVIDENCE = frozenset({"log_refs", "validation_command_refs", "observed_at"})


class JobFailureSchemaError(ValueError):
    """Raised when a job-failure record violates its local schema."""


def validate_job_failure_document(document: object) -> dict[str, Any]:
    """Validate one failure record without reading referenced local evidence."""

    failure = _object(document, "job failure", _REQUIRED)
    if (
        not isinstance(failure["schema_version"], int)
        or isinstance(failure["schema_version"], bool)
        or failure["schema_version"] != JOB_FAILURE_SCHEMA_VERSION
    ):
        raise JobFailureSchemaError("job failure.schema_version must be integer 1")
    for field in (
        "failure_id",
        "job_id",
        "creator_node_id",
        "executing_node_id",
    ):
        _identifier(failure[field], f"job failure.{field}")
    if failure["task_id"] is not None:
        _identifier(failure["task_id"], "job failure.task_id")
    _timestamp(failure["observed_at"], "job failure.observed_at")
    _choice(failure, "failure_type", FAILURE_TYPES)
    _choice(failure, "failure_stage", FAILURE_STAGES)
    _choice(failure, "severity", SEVERITIES)
    if not isinstance(failure["retryable"], bool):
        raise JobFailureSchemaError("job failure.retryable must be a boolean")
    summary = failure["human_summary"]
    if not isinstance(summary, str) or not summary or len(summary) > 512:
        raise JobFailureSchemaError(
            "job failure.human_summary must be a non-empty string up to 512 characters"
        )
    _details(failure["details"])
    _links(failure["links"])
    _attribution(failure["attribution"])
    _evidence(failure["evidence"])
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
        or any(map(str.isspace, value))
        or value.strip() != value
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


def _choice(document: dict[str, Any], field: str, choices: frozenset[str]) -> None:
    if document[field] not in choices:
        raise JobFailureSchemaError(
            f"job failure.{field} must be one of {', '.join(sorted(choices))}"
        )


def _optional_identifier(value: object, context: str) -> None:
    if value is not None:
        _identifier(value, context)


def _optional_hash(value: object, context: str) -> None:
    if value is not None and (
        not isinstance(value, str)
        or len(value) != 71
        or not value.startswith("sha256:")
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise JobFailureSchemaError(f"{context} must be a sha256 hash or null")


def _details(value: object) -> None:
    details = _object(value, "job failure.details", _DETAILS)
    for field in ("exit_code", "timeout_ms"):
        item = details[field]
        if item is not None and (
            not isinstance(item, int) or isinstance(item, bool) or item < 0
        ):
            raise JobFailureSchemaError(
                f"job failure.details.{field} must be non-negative or null"
            )
    for field in (
        "signal",
        "validation_error_code",
        "missing_input_id",
        "expected_receipt_id",
        "observed_receipt_id",
        "environment_issue_code",
    ):
        _optional_identifier(details[field], f"job failure.details.{field}")
    for field in ("expected_manifest_hash", "observed_manifest_hash"):
        _optional_hash(details[field], f"job failure.details.{field}")
    if all(item is None for item in details.values()):
        raise JobFailureSchemaError(
            "job failure.details must contain machine-readable evidence"
        )


def _links(value: object) -> None:
    links = _object(value, "job failure.links", _LINKS)
    for field in ("job_manifest_hash", "input_manifest_hash"):
        _optional_hash(links[field], f"job failure.links.{field}")
        if links[field] is None:
            raise JobFailureSchemaError(f"job failure.links.{field} is required")
    _optional_hash(
        links["output_manifest_hash"], "job failure.links.output_manifest_hash"
    )
    for field in (
        "validation_receipt_ids",
        "lineage_parent_ids",
        "attribution_record_ids",
    ):
        _identifier_list(links[field], f"job failure.links.{field}")


def _attribution(value: object) -> None:
    attribution = _object(value, "job failure.attribution", _ATTRIBUTION)
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
    if amount == 0 and (not isinstance(reason, str) or not reason):
        raise JobFailureSchemaError(
            "job failure.attribution.rejection_reason is required when no work is accepted"
        )
    if reason is not None and not isinstance(reason, str):
        raise JobFailureSchemaError(
            "job failure.attribution.rejection_reason must be a string or null"
        )


def _evidence(value: object) -> None:
    evidence = _object(value, "job failure.evidence", _EVIDENCE)
    _timestamp(evidence["observed_at"], "job failure.evidence.observed_at")
    _identifier_list(
        evidence["validation_command_refs"],
        "job failure.evidence.validation_command_refs",
    )
    refs = evidence["log_refs"]
    if not isinstance(refs, list) or not refs:
        raise JobFailureSchemaError(
            "job failure.evidence.log_refs must contain an evidence reference"
        )
    for index, ref in enumerate(refs):
        item = _object(
            ref,
            f"job failure.evidence.log_refs[{index}]",
            frozenset({"path", "sha256"}),
        )
        path = item["path"]
        if path is not None and (
            not isinstance(path, str)
            or not path
            or path.startswith(("/", "\\"))
            or "\\" in path
            or ".." in path.split("/")
        ):
            raise JobFailureSchemaError(
                "evidence paths must be safe relative local paths"
            )
        _optional_hash(item["sha256"], "job failure.evidence.log_refs.sha256")
        if path is None and item["sha256"] is None:
            raise JobFailureSchemaError(
                "each evidence reference needs a path or content hash"
            )


def _identifier_list(value: object, context: str) -> None:
    if not isinstance(value, list):
        raise JobFailureSchemaError(f"{context} must be a list")
    for item in value:
        _identifier(item, f"{context} entries")
