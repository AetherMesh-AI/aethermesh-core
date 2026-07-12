"""Strict local-only capability record schema validation."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

CAPABILITY_RECORD_SCHEMA_VERSION = 1
CAPABILITY_TYPES = frozenset({"model", "tool", "validator", "worker", "work"})
VALIDATION_STATUSES = frozenset({"unvalidated", "passed", "failed", "stale"})
_CAPABILITY_ID = re.compile(r"^local-capability-[A-Za-z0-9][A-Za-z0-9._-]*$")
_RECEIPT_ID = re.compile(r"^local-validation-receipt-[A-Za-z0-9][A-Za-z0-9._-]*$")
_REFERENCE = re.compile(
    r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9][A-Za-z0-9._/-]*(?:#[A-Za-z0-9._:-]+)?$"
)


class CapabilityRecordError(ValueError):
    """Raised when a local capability record is incomplete or misleading."""


def validate_capability_record(document: object) -> dict[str, Any]:
    """Validate and return a copy of a version-one local capability record."""
    record = _object(document, "capability record")
    _exact_keys(
        record,
        {
            "schema_version",
            "capability_id",
            "creator_node_id",
            "created_at",
            "updated_at",
            "metadata",
            "manifest_references",
            "validation",
            "lineage",
            "contribution_attribution",
        },
        "capability record",
    )
    _integer(
        record["schema_version"], "schema_version", CAPABILITY_RECORD_SCHEMA_VERSION
    )
    _pattern(record["capability_id"], "capability_id", _CAPABILITY_ID)
    _string(record["creator_node_id"], "creator_node_id")
    _timestamp(record["created_at"], "created_at")
    _timestamp(record["updated_at"], "updated_at")
    _metadata(record["metadata"])
    _manifest_references(record["manifest_references"])
    _validation(record["validation"])
    _lineage(record["lineage"])
    _attribution(record["contribution_attribution"], record["creator_node_id"])
    return dict(record)


def _metadata(value: object) -> None:
    metadata = _object(value, "metadata")
    _exact_keys(
        metadata,
        {
            "name",
            "description",
            "capability_type",
            "supported_input_formats",
            "supported_output_formats",
            "constraints",
            "local_execution_requirements",
        },
        "metadata",
    )
    _string(metadata["name"], "metadata.name")
    _string(metadata["description"], "metadata.description")
    capability_type = _string(metadata["capability_type"], "metadata.capability_type")
    if capability_type not in CAPABILITY_TYPES:
        raise CapabilityRecordError("metadata.capability_type has an unknown value")
    _string_list(
        metadata["supported_input_formats"], "metadata.supported_input_formats"
    )
    _string_list(
        metadata["supported_output_formats"], "metadata.supported_output_formats"
    )
    _object(metadata["constraints"], "metadata.constraints")
    requirements = _object(
        metadata["local_execution_requirements"],
        "metadata.local_execution_requirements",
    )
    _exact_keys(
        requirements,
        {"execution_scope", "requirements"},
        "metadata.local_execution_requirements",
    )
    if requirements["execution_scope"] != "local-only":
        raise CapabilityRecordError(
            "metadata.local_execution_requirements.execution_scope must be local-only"
        )
    _string_list(
        requirements["requirements"],
        "metadata.local_execution_requirements.requirements",
    )


def _manifest_references(value: object) -> None:
    references = _object(value, "manifest_references")
    _exact_keys(
        references,
        {"node_manifest_ref", "runtime_manifest_ref", "backing_manifest_refs"},
        "manifest_references",
    )
    _reference(references["node_manifest_ref"], "manifest_references.node_manifest_ref")
    _reference(
        references["runtime_manifest_ref"], "manifest_references.runtime_manifest_ref"
    )
    _reference_list(
        references["backing_manifest_refs"], "manifest_references.backing_manifest_refs"
    )


def _validation(value: object) -> None:
    validation = _object(value, "validation")
    _exact_keys(
        validation,
        {"status", "receipt_ids", "last_validated_at", "check_name", "failure_reason"},
        "validation",
    )
    status = _string(validation["status"], "validation.status")
    if status not in VALIDATION_STATUSES:
        raise CapabilityRecordError("validation.status has an unknown value")
    receipt_ids = validation["receipt_ids"]
    _receipt_list(receipt_ids)
    if status == "unvalidated":
        if receipt_ids or any(
            validation[field] is not None
            for field in ("last_validated_at", "check_name", "failure_reason")
        ):
            raise CapabilityRecordError(
                "unvalidated capabilities must not present validation evidence"
            )
        return
    if not receipt_ids:
        raise CapabilityRecordError(
            "validated capabilities require validation.receipt_ids"
        )
    _timestamp(validation["last_validated_at"], "validation.last_validated_at")
    _string(validation["check_name"], "validation.check_name")
    if status == "failed":
        _string(validation["failure_reason"], "validation.failure_reason")
    elif validation["failure_reason"] is not None:
        raise CapabilityRecordError(
            "only failed capabilities may include validation.failure_reason"
        )


def _lineage(value: object) -> None:
    lineage = _object(value, "lineage")
    _exact_keys(
        lineage,
        {"source_manifest_ref", "prior_capability_id", "local_build_artifact_ref"},
        "lineage",
    )
    _reference(lineage["source_manifest_ref"], "lineage.source_manifest_ref")
    _nullable_pattern(
        lineage["prior_capability_id"], "lineage.prior_capability_id", _CAPABILITY_ID
    )
    _nullable_reference(
        lineage["local_build_artifact_ref"], "lineage.local_build_artifact_ref"
    )


def _attribution(value: object, creator_node_id: object) -> None:
    attribution = _object(value, "contribution_attribution")
    _exact_keys(
        attribution,
        {"creator_node_id", "maintainer_node_id", "local_work_receipt_ids"},
        "contribution_attribution",
    )
    if attribution["creator_node_id"] != creator_node_id:
        raise CapabilityRecordError(
            "contribution_attribution.creator_node_id must match creator_node_id"
        )
    _string(
        attribution["maintainer_node_id"], "contribution_attribution.maintainer_node_id"
    )
    _receipt_list(attribution["local_work_receipt_ids"])


def _object(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CapabilityRecordError(f"{field} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise CapabilityRecordError(
            f"{field} must contain exactly the documented fields"
        )


def _integer(value: object, field: str, expected: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value != expected:
        raise CapabilityRecordError(f"{field} must be integer {expected}")


def _string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CapabilityRecordError(f"{field} must be a non-empty string")
    return value


def _pattern(value: object, field: str, pattern: re.Pattern[str]) -> None:
    if pattern.fullmatch(_string(value, field)) is None:
        raise CapabilityRecordError(f"{field} has an invalid format")


def _reference(value: object, field: str) -> None:
    _pattern(value, field, _REFERENCE)


def _nullable_reference(value: object, field: str) -> None:
    if value is not None:
        _reference(value, field)


def _nullable_pattern(value: object, field: str, pattern: re.Pattern[str]) -> None:
    if value is not None:
        _pattern(value, field, pattern)


def _string_list(value: object, field: str) -> None:
    if not isinstance(value, list) or not value:
        raise CapabilityRecordError(f"{field} must be a non-empty list of strings")
    for item in value:
        _string(item, field)


def _reference_list(value: object, field: str) -> None:
    if not isinstance(value, list) or not value:
        raise CapabilityRecordError(
            f"{field} must be a non-empty list of local references"
        )
    for item in value:
        _reference(item, field)


def _receipt_list(value: object) -> None:
    if not isinstance(value, list):
        raise CapabilityRecordError("validation receipt IDs must be a list")
    for item in value:
        _pattern(item, "validation receipt ID", _RECEIPT_ID)


def _timestamp(value: object, field: str) -> None:
    timestamp = _string(value, field)
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CapabilityRecordError(f"{field} must be an ISO 8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise CapabilityRecordError(f"{field} must be a UTC timestamp")
