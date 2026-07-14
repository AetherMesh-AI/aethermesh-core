"""Validation for the local-only version 1 contribution record contract."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from aethermesh_core.scheduler import SUPPORTED_LOCAL_JOB_TYPES

CONTRIBUTION_RECORD_SCHEMA_VERSION = 1
VALIDATION_STATUSES = frozenset({"unvalidated", "passed", "failed"})
AUTHOR_KINDS = frozenset({"human", "node"})
CREATION_MODES = frozenset({"manual", "automatic"})
PHASE1_JOB_CAPABILITIES = {job_type: job_type for job_type in SUPPORTED_LOCAL_JOB_TYPES}
_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "record_id",
        "job_id",
        "creator_node_id",
        "contributor_node_id",
        "created_at",
        "work_type",
        "job_type",
        "capability",
        "contribution_summary",
        "source",
        "manifest_links",
        "validation",
        "lineage",
        "attribution",
    }
)
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9_.-]{2,127}\Z")
_LOCAL_JOB_ID = re.compile(r"local-job-[0-9a-f]{32}\Z")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
_URI_SCHEME = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*:")


class ContributionRecordError(ValueError):
    """Raised when a local contribution record violates its stable contract."""


def validate_contribution_record(document: object) -> dict[str, Any]:
    """Validate a local contribution record without implying network consensus."""
    if not isinstance(document, dict):
        raise ContributionRecordError("contribution record must be an object")
    _exact_fields(document, _TOP_LEVEL_FIELDS, "contribution record")
    _require_int(document, "schema_version", CONTRIBUTION_RECORD_SCHEMA_VERSION)
    for field in ("record_id", "creator_node_id", "contributor_node_id"):
        _require_identifier(document, field)
    _require_local_job_id(document, "job_id")
    _require_timestamp(document, "created_at")
    _require_string(document, "work_type")
    _job_metadata(document)
    _require_string(document, "contribution_summary")
    _source(document["source"])
    _manifest_links(document["manifest_links"])
    _validation(document["validation"])
    _lineage(document["lineage"], document["contributor_node_id"])
    _attribution(document["attribution"])
    return document


def _job_metadata(document: dict[str, Any]) -> None:
    job_type = _require_string(document, "job_type")
    capability = _require_string(document, "capability")
    expected_capability = PHASE1_JOB_CAPABILITIES.get(job_type)
    if expected_capability is None:
        raise ContributionRecordError("job_type is not an allowed Phase 1 work type")
    if capability != expected_capability:
        raise ContributionRecordError(
            "capability must match the local manifest capability for job_type"
        )


def _exact_fields(value: object, fields: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContributionRecordError(f"{label} must be an object")
    missing = sorted(fields - value.keys())
    if missing:
        raise ContributionRecordError(f"{label} missing: {', '.join(missing)}")
    unknown = sorted(value.keys() - fields)
    if unknown:
        raise ContributionRecordError(
            f"{label} contains unsupported fields: {', '.join(unknown)}"
        )
    return value


def _require_int(document: dict[str, Any], field: str, expected: int) -> None:
    if document.get(field) != expected or isinstance(document.get(field), bool):
        raise ContributionRecordError(f"{field} must be integer {expected}")


def _require_identifier(document: dict[str, Any], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ContributionRecordError(f"{field} must be a stable local identifier")
    return value


def _require_local_job_id(document: dict[str, Any], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not _LOCAL_JOB_ID.fullmatch(value):
        raise ContributionRecordError(
            f"{field} must be a local-job- followed by 32 lowercase hex characters"
        )
    return value


def _require_string(document: dict[str, Any], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContributionRecordError(f"{field} must be a non-empty string")
    return value


def _require_timestamp(document: dict[str, Any], field: str) -> None:
    value = _require_string(document, field)
    if not _TIMESTAMP.fullmatch(value):
        raise ContributionRecordError(f"{field} must be an RFC 3339 UTC timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ContributionRecordError(
            f"{field} must be an RFC 3339 UTC timestamp"
        ) from exc


def _source(value: object) -> None:
    source = _exact_fields(
        value, frozenset({"local_source_path", "artifact_ref"}), "source"
    )
    _optional_ref(source, "local_source_path")
    _optional_ref(source, "artifact_ref")
    if source["local_source_path"] is None and source["artifact_ref"] is None:
        raise ContributionRecordError(
            "source requires local_source_path or artifact_ref"
        )


def _manifest_links(value: object) -> None:
    links = _exact_fields(
        value,
        frozenset(
            {
                "node_manifest_ref",
                "work_manifest_ref",
                "input_manifest_ref",
                "output_manifest_ref",
                "validation_manifest_ref",
            }
        ),
        "manifest_links",
    )
    for field in links:
        _optional_ref(links, field)


def _validation(value: object) -> None:
    validation = _exact_fields(
        value,
        frozenset(
            {
                "status",
                "validator_node_id",
                "validation_receipt_ref",
                "validated_at",
                "failure_reason",
            }
        ),
        "validation",
    )
    status = _require_string(validation, "status")
    if status not in VALIDATION_STATUSES:
        raise ContributionRecordError("validation.status is not allowed")
    _optional_identifier(validation, "validator_node_id")
    _optional_ref(validation, "validation_receipt_ref")
    _optional_timestamp(validation, "validated_at")
    _optional_string(validation, "failure_reason")
    if status == "failed" and validation["failure_reason"] is None:
        raise ContributionRecordError("failed validation requires failure_reason")
    if status != "failed" and validation["failure_reason"] is not None:
        raise ContributionRecordError(
            "only failed validation may include failure_reason"
        )


def _lineage(value: object, document_contributor_node_id: str) -> None:
    lineage = _exact_fields(
        value,
        frozenset(
            {
                "contributor_node_id",
                "parent_contribution_ids",
                "derived_artifact_ids",
                "input_hashes",
                "output_hashes",
                "deterministic_reproduction_notes",
            }
        ),
        "lineage",
    )
    for field in ("parent_contribution_ids", "derived_artifact_ids"):
        _identifier_list(lineage, field)
    _require_identifier(lineage, "contributor_node_id")
    for field in ("input_hashes", "output_hashes"):
        _sha256_list(lineage, field)
    _optional_string(lineage, "deterministic_reproduction_notes")
    if lineage["contributor_node_id"] != document_contributor_node_id:
        raise ContributionRecordError(
            "lineage.contributor_node_id must match contributor_node_id"
        )


def _attribution(value: object) -> None:
    attribution = _exact_fields(
        value,
        frozenset(
            {
                "author_id",
                "author_kind",
                "role",
                "declared_tool_or_runtime",
                "creation_mode",
            }
        ),
        "attribution",
    )
    _require_identifier(attribution, "author_id")
    if _require_string(attribution, "author_kind") not in AUTHOR_KINDS:
        raise ContributionRecordError("attribution.author_kind is not allowed")
    _require_string(attribution, "role")
    _optional_string(attribution, "declared_tool_or_runtime")
    if _require_string(attribution, "creation_mode") not in CREATION_MODES:
        raise ContributionRecordError("attribution.creation_mode is not allowed")


def _optional_identifier(document: dict[str, Any], field: str) -> None:
    if document.get(field) is not None:
        _require_identifier(document, field)


def _identifier_list(document: dict[str, Any], field: str) -> None:
    _matching_string_list(document, field, _IDENTIFIER, "a stable local identifier")


def _sha256_list(document: dict[str, Any], field: str) -> None:
    _matching_string_list(document, field, _SHA256, "a lowercase SHA-256 digest")


def _matching_string_list(
    document: dict[str, Any],
    field: str,
    pattern: re.Pattern[str],
    description: str,
) -> None:
    values = document.get(field)
    if not isinstance(values, list):
        raise ContributionRecordError(f"{field} must be a list")
    for index, value in enumerate(values):
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise ContributionRecordError(f"{field}[{index}] must be {description}")


def _optional_ref(document: dict[str, Any], field: str) -> None:
    value = document.get(field)
    if value is None:
        return
    if (
        not isinstance(value, str)
        or not value
        or value.startswith(("/", "~"))
        or "\\" in value
        or ".." in value.split("/")
        or _URI_SCHEME.match(value)
    ):
        raise ContributionRecordError(
            f"{field} must be a safe local relative reference"
        )


def _optional_timestamp(document: dict[str, Any], field: str) -> None:
    if document.get(field) is not None:
        _require_timestamp(document, field)


def _optional_string(document: dict[str, Any], field: str) -> None:
    if document.get(field) is not None:
        _require_string(document, field)
