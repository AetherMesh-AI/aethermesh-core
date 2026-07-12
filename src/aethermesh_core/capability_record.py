"""Validation for the local-only version 1 capability record contract."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

CAPABILITY_RECORD_SCHEMA_VERSION = 1
CAPABILITY_TYPES = frozenset({"model", "tool", "worker", "runtime"})
VALIDATION_STATUSES = frozenset({"unvalidated", "passed", "failed"})
_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema_version",
        "capability_id",
        "capability_version",
        "node_id",
        "creator_node_id",
        "created_at",
        "updated_at",
        "metadata",
        "manifest_refs",
        "validation",
        "lineage",
        "contribution_attribution",
    }
)
_IDENTIFIER = re.compile(r"[a-z][a-z0-9_.-]{2,127}\Z")
_CAPABILITY_VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\Z")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_URI_SCHEME = re.compile(r"[a-zA-Z][a-zA-Z0-9+.-]*:")


class CapabilityRecordError(ValueError):
    """Raised when a local capability record is incomplete or dishonest."""


def validate_capability_record(
    document: object, *, local_node_id: str
) -> dict[str, Any]:
    """Validate and return one local-only capability record without writing it.

    A passed claim requires local receipt evidence; an unvalidated claim is
    accepted only as explicitly untrusted local metadata.
    """
    if not isinstance(document, dict):
        raise CapabilityRecordError("capability record must be an object")
    _reject_unknown_fields(document)
    _require_int(document, "schema_version", CAPABILITY_RECORD_SCHEMA_VERSION)
    _require_identifier(document, "capability_id")
    _require_capability_version(document)
    node_id = _require_identifier(document, "node_id")
    if node_id != _require_identifier_value(local_node_id, "local_node_id"):
        raise CapabilityRecordError("node_id must match the local node identity")
    _require_identifier(document, "creator_node_id")
    _require_timestamp(document, "created_at")
    _require_timestamp(document, "updated_at")
    _require_metadata(document)
    _require_ref_list(document, "manifest_refs", minimum=1)
    _require_lineage(document)
    _require_attribution(document)
    _require_validation(document)
    return document


def _reject_unknown_fields(document: dict[str, Any]) -> None:
    allowed_by_field = {
        "metadata": frozenset(
            {
                "name",
                "description",
                "type",
                "supported_input_formats",
                "supported_output_formats",
                "constraints",
                "local_execution_requirements",
            }
        ),
        "validation": frozenset(
            {
                "status",
                "receipt_ids",
                "last_validated_at",
                "check_name",
                "failure_reason",
            }
        ),
        "lineage": frozenset(
            {"source_manifest_ref", "prior_capability_id", "local_build_artifact_ref"}
        ),
        "contribution_attribution": frozenset(
            {"creator_node_id", "maintainer_node_id", "work_receipt_ids"}
        ),
    }
    unknown = sorted(document.keys() - _TOP_LEVEL_FIELDS)
    if unknown:
        raise CapabilityRecordError(
            f"capability record contains unsupported fields: {', '.join(unknown)}"
        )
    for field, allowed in allowed_by_field.items():
        value = document.get(field)
        if isinstance(value, dict):
            unknown = sorted(value.keys() - allowed)
            if unknown:
                raise CapabilityRecordError(
                    f"{field} contains unsupported fields: {', '.join(unknown)}"
                )


def _require_metadata(document: dict[str, Any]) -> None:
    metadata = _require_object(document, "metadata")
    _require_string(metadata, "name")
    _require_string(metadata, "description")
    capability_type = _require_string(metadata, "type")
    if capability_type not in CAPABILITY_TYPES:
        raise CapabilityRecordError("metadata.type is not allowed")
    _require_string_list(metadata, "supported_input_formats", minimum=1)
    _require_string_list(metadata, "supported_output_formats", minimum=1)
    if not isinstance(metadata.get("constraints"), dict):
        raise CapabilityRecordError("metadata.constraints must be an object")
    _require_string_list(metadata, "local_execution_requirements", minimum=1)


def _require_validation(document: dict[str, Any]) -> None:
    validation = _require_object(document, "validation")
    status = _require_string(validation, "status")
    if status not in VALIDATION_STATUSES:
        raise CapabilityRecordError("validation.status is not allowed")
    _require_identifier_list(validation, "receipt_ids")
    if status == "passed":
        if not validation["receipt_ids"]:
            raise CapabilityRecordError("passed validation requires a receipt ID")
        _require_timestamp(validation, "last_validated_at")
        _require_string(validation, "check_name")
        if "failure_reason" in validation:
            raise CapabilityRecordError(
                "passed validation must not include failure_reason"
            )
    elif status == "failed":
        _require_timestamp(validation, "last_validated_at")
        _require_string(validation, "check_name")
        _require_string(validation, "failure_reason")
    else:
        if validation["receipt_ids"]:
            raise CapabilityRecordError(
                "unvalidated capability must not claim receipt IDs"
            )
        for field in ("last_validated_at", "check_name", "failure_reason"):
            if field in validation:
                raise CapabilityRecordError(
                    f"unvalidated capability must not include {field}"
                )


def _require_lineage(document: dict[str, Any]) -> None:
    lineage = _require_object(document, "lineage")
    _require_ref(lineage, "source_manifest_ref")
    _require_optional_identifier(lineage, "prior_capability_id")
    _require_optional_ref(lineage, "local_build_artifact_ref")


def _require_attribution(document: dict[str, Any]) -> None:
    attribution = _require_object(document, "contribution_attribution")
    if (
        _require_identifier(attribution, "creator_node_id")
        != document["creator_node_id"]
    ):
        raise CapabilityRecordError(
            "attribution creator_node_id must match creator_node_id"
        )
    _require_identifier(attribution, "maintainer_node_id")
    _require_identifier_list(attribution, "work_receipt_ids")


def _require_object(document: dict[str, Any], field: str) -> dict[str, Any]:
    value = document.get(field)
    if not isinstance(value, dict):
        raise CapabilityRecordError(f"{field} must be an object")
    return value


def _require_string(document: dict[str, Any], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        raise CapabilityRecordError(f"{field} must be a non-empty string")
    return value


def _require_int(document: dict[str, Any], field: str, expected: int) -> None:
    value = document.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value != expected:
        raise CapabilityRecordError(f"{field} must be integer {expected}")


def _require_identifier(document: dict[str, Any], field: str) -> str:
    return _require_identifier_value(document.get(field), field)


def _require_capability_version(document: dict[str, Any]) -> None:
    value = _require_string(document, "capability_version")
    if not _CAPABILITY_VERSION.fullmatch(value):
        raise CapabilityRecordError(
            "capability_version must be a semantic version (major.minor.patch)"
        )


def _require_identifier_value(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CapabilityRecordError(f"{field} must be a non-empty string")
    if not _IDENTIFIER.fullmatch(value):
        raise CapabilityRecordError(f"{field} must be a stable local identifier")
    return value


def _require_timestamp(document: dict[str, Any], field: str) -> None:
    value = _require_string(document, field)
    if not _TIMESTAMP.fullmatch(value):
        raise CapabilityRecordError(f"{field} must be an RFC 3339 UTC timestamp")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise CapabilityRecordError(
            f"{field} must be an RFC 3339 UTC timestamp"
        ) from exc


def _require_ref_list(
    document: dict[str, Any], field: str, *, minimum: int = 0
) -> None:
    values = document.get(field)
    if not isinstance(values, list) or len(values) < minimum:
        raise CapabilityRecordError(
            f"{field} must be a list with at least {minimum} item(s)"
        )
    for index, value in enumerate(values):
        _require_safe_ref(value, f"{field}[{index}]")


def _require_identifier_list(document: dict[str, Any], field: str) -> None:
    values = document.get(field)
    if not isinstance(values, list):
        raise CapabilityRecordError(f"{field} must be a list")
    for index, value in enumerate(values):
        if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
            raise CapabilityRecordError(
                f"{field}[{index}] must be a stable local identifier"
            )


def _require_string_list(document: dict[str, Any], field: str, *, minimum: int) -> None:
    values = document.get(field)
    if not isinstance(values, list) or len(values) < minimum:
        raise CapabilityRecordError(
            f"{field} must be a list with at least {minimum} item(s)"
        )
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise CapabilityRecordError(f"{field}[{index}] must be a non-empty string")


def _require_ref(document: dict[str, Any], field: str) -> None:
    _require_safe_ref(document.get(field), field)


def _require_optional_identifier(document: dict[str, Any], field: str) -> None:
    if field in document and document[field] is not None:
        _require_identifier(document, field)


def _require_optional_ref(document: dict[str, Any], field: str) -> None:
    if field in document and document[field] is not None:
        _require_ref(document, field)


def _require_safe_ref(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith(("/", "~"))
        or "\\" in value
        or ".." in value.split("/")
        or _URI_SCHEME.match(value)
    ):
        raise CapabilityRecordError(f"{field} must be a safe local relative reference")
