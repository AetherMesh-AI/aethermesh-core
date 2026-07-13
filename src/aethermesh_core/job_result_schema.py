"""Validation for local, auditable Phase 1 result report records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

JOB_RESULT_SCHEMA_VERSION = 1
RESULT_STATUSES = frozenset(
    {
        "succeeded",
        "failed",
        "timed_out",
        "cancelled",
        "validation_failed",
        "partially_completed",
    }
)
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
_REFERENCE_FIELDS = frozenset(
    {"manifest_hash", "artifact_refs", "validation_receipt_ids", "log_refs"}
)
_CONTRIBUTION_FIELDS = frozenset(
    {
        "creator_node_id",
        "executor_node_id",
        "validator_node_id",
        "upstream_lineage_sources",
        "local_operator_id",
    }
)
_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "result_id",
        "job_id",
        "task_id",
        "creator_node_id",
        "executor_node_id",
        "manifest_id",
        "references",
        "created_at",
        "status",
        "exit_code",
        "started_at",
        "finished_at",
        "duration_ms",
        "summary",
        "error_summary",
        "validation_status",
        "validation_receipt_id",
        "validator_node_id",
        "failure_reasons",
        "lineage",
        "contribution",
    }
)


class JobResultSchemaError(ValueError):
    """Raised when a local result report violates its stable schema."""


def validate_job_result_document(document: object) -> dict[str, Any]:
    """Validate one local-only result report without reading or writing files."""

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
        raise JobResultSchemaError("job result.status is unsupported")
    if not isinstance(result["exit_code"], int) or isinstance(
        result["exit_code"], bool
    ):
        raise JobResultSchemaError("job result.exit_code must be an integer")
    _summary(result["summary"], "job result.summary", nullable=False)
    _summary(result["error_summary"], "job result.error_summary", nullable=True)
    if result["status"] != "succeeded" and result["error_summary"] is None:
        raise JobResultSchemaError(
            "job result.error_summary is required when the job did not succeed"
        )
    if result["validation_status"] not in VALIDATION_STATUSES:
        raise JobResultSchemaError("job result.validation_status is unsupported")
    _references(
        result["references"], result["manifest_id"], result["validation_receipt_id"]
    )
    _failure_reasons(result["failure_reasons"])
    _lineage(result["lineage"])
    _contribution(
        result["contribution"],
        result["creator_node_id"],
        result["executor_node_id"],
        result["validator_node_id"],
        result["lineage"],
    )
    return result


def _object(value: object, context: str, required: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise JobResultSchemaError(f"{context} must be an object")
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
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
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise JobResultSchemaError(f"{context} must be a UTC timestamp") from exc


def _exact_integer(value: object, context: str, expected: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value != expected:
        raise JobResultSchemaError(f"{context} must be integer {expected}")


def _summary(value: object, context: str, *, nullable: bool) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not value or len(value) > 512:
        suffix = " or null" if nullable else ""
        raise JobResultSchemaError(
            f"{context} must be a non-empty string up to 512 characters{suffix}"
        )


def _failure_reasons(value: object) -> None:
    reasons = _object(value, "job result.failure_reasons", _FAILURE_FIELDS)
    for field, reason in reasons.items():
        if reason is not None and (not isinstance(reason, str) or not reason):
            raise JobResultSchemaError(
                f"job result.failure_reasons.{field} must be a non-empty string or null"
            )


def _references(value: object, manifest_id: object, receipt_id: object) -> None:
    references = _object(value, "job result.references", _REFERENCE_FIELDS)
    if references["manifest_hash"] != manifest_id:
        raise JobResultSchemaError(
            "job result.references.manifest_hash must match manifest_id"
        )
    _content_addressed_id(
        references["manifest_hash"], "job result.references.manifest_hash"
    )
    for field in ("artifact_refs", "log_refs"):
        _artifact_reference_list(references[field], f"job result.references.{field}")
    _identifier_list(
        references["validation_receipt_ids"],
        "job result.references.validation_receipt_ids",
    )
    if receipt_id not in references["validation_receipt_ids"]:
        raise JobResultSchemaError(
            "job result.references.validation_receipt_ids must include validation_receipt_id"
        )


def _content_addressed_id(value: object, context: str) -> None:
    if (
        not isinstance(value, str)
        or not value.startswith("sha256:")
        or len(value) != 71
        or any(character not in "0123456789abcdef" for character in value[7:])
    ):
        raise JobResultSchemaError(f"{context} must be a SHA-256 content-addressed ID")


def _artifact_reference_list(value: object, context: str) -> None:
    if not isinstance(value, list):
        raise JobResultSchemaError(f"{context} must be a list")
    for reference in value:
        if not isinstance(reference, str) or not reference:
            raise JobResultSchemaError(f"{context} entries must be local references")
        if reference.startswith("sha256:"):
            _content_addressed_id(reference, f"{context} entries")
        elif (
            reference.startswith(("/", "~"))
            or "://" in reference
            or "\\" in reference
            or any(part == ".." for part in reference.split("/"))
        ):
            raise JobResultSchemaError(
                f"{context} entries must be relative local paths or content-addressed IDs"
            )


def _identifier_list(value: object, context: str) -> None:
    if not isinstance(value, list):
        raise JobResultSchemaError(f"{context} must be a list")
    for item in value:
        _identifier(item, f"{context} entries")


def _lineage(value: object) -> None:
    lineage = _object(value, "job result.lineage", _LINEAGE_FIELDS)
    for field, references in lineage.items():
        _identifier_list(references, f"job result.lineage.{field}")


def _contribution(
    value: object,
    creator_node_id: object,
    executor_node_id: object,
    validator_node_id: object,
    lineage: object,
) -> None:
    contribution = _object(value, "job result.contribution", _CONTRIBUTION_FIELDS)
    for field, expected in (
        ("creator_node_id", creator_node_id),
        ("executor_node_id", executor_node_id),
        ("validator_node_id", validator_node_id),
    ):
        if contribution[field] != expected:
            raise JobResultSchemaError(
                f"job result.contribution.{field} must match the top-level record"
            )
        _identifier(contribution[field], f"job result.contribution.{field}")
    _identifier_list(
        contribution["upstream_lineage_sources"],
        "job result.contribution.upstream_lineage_sources",
    )
    if (
        not isinstance(lineage, dict)
        or contribution["upstream_lineage_sources"] != lineage["parent_job_ids"]
    ):
        raise JobResultSchemaError(
            "job result.contribution.upstream_lineage_sources must match lineage.parent_job_ids"
        )
    operator = contribution["local_operator_id"]
    if operator is not None:
        _identifier(operator, "job result.contribution.local_operator_id")
