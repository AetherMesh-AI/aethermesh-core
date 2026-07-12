"""Validation for the local-only version 1 capability record contract."""

from __future__ import annotations

import re
from typing import Any

CAPABILITY_RECORD_SCHEMA_VERSION = 1
CAPABILITY_TYPES = frozenset({"model", "tool", "worker", "runtime"})
VALIDATION_STATUSES = frozenset({"unvalidated", "passed", "failed"})
_IDENTIFIER = re.compile(r"[a-z][a-z0-9_.-]{2,127}\Z")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


class CapabilityRecordError(ValueError):
    """Raised when a local capability record is incomplete or dishonest."""


def validate_capability_record(document: object) -> dict[str, Any]:
    """Validate and return one local-only capability record without writing it.

    A passed claim requires local receipt evidence; an unvalidated claim is
    accepted only as explicitly untrusted local metadata.
    """
    if not isinstance(document, dict):
        raise CapabilityRecordError("capability record must be an object")
    _require_int(document, "schema_version", CAPABILITY_RECORD_SCHEMA_VERSION)
    _require_identifier(document, "capability_id")
    _require_identifier(document, "creator_node_id")
    _require_timestamp(document, "created_at")
    _require_timestamp(document, "updated_at")
    _require_metadata(document)
    _require_ref_list(document, "manifest_refs", minimum=1)
    _require_lineage(document)
    _require_attribution(document)
    _require_validation(document)
    return document


def _require_metadata(document: dict[str, Any]) -> None:
    metadata = _require_object(document, "metadata")
    _require_string(metadata, "name")
    _require_string(metadata, "description")
    capability_type = _require_string(metadata, "capability_type")
    if capability_type not in CAPABILITY_TYPES:
        raise CapabilityRecordError("metadata.capability_type is not allowed")
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
    elif status == "failed":
        _require_timestamp(validation, "last_validated_at")
        _require_string(validation, "check_name")
        _require_string(validation, "failure_reason")
    elif validation["receipt_ids"]:
        raise CapabilityRecordError("unvalidated capability must not claim receipt IDs")


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
    value = _require_string(document, field)
    if not _IDENTIFIER.fullmatch(value):
        raise CapabilityRecordError(f"{field} must be a stable local identifier")
    return value


def _require_timestamp(document: dict[str, Any], field: str) -> None:
    if not _TIMESTAMP.fullmatch(_require_string(document, field)):
        raise CapabilityRecordError(f"{field} must be an RFC 3339 UTC timestamp")


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
        or ".." in value
        or "://" in value
    ):
        raise CapabilityRecordError(f"{field} must be a safe local relative reference")
