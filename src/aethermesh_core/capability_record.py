"""Validation for versioned, local-only capability records."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

CAPABILITY_RECORD_SCHEMA_VERSION = 1
CAPABILITY_TYPES = frozenset({"model", "tool", "worker", "runtime"})
VALIDATION_STATUSES = frozenset({"unvalidated", "pending", "passed", "failed"})
MANIFEST_KINDS = frozenset({"node", "runtime", "model", "tool", "worker"})

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9-]{0,127}$")
_RECEIPT_ID = re.compile(r"^local-validation-receipt-[a-z0-9][a-z0-9-]{0,127}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class CapabilityRecordError(ValueError):
    """Raised when a local capability record is incomplete or unsafe."""


def validate_capability_record(document: Any) -> dict[str, Any]:
    """Validate and copy one local-only capability record version 1.

    This checks record structure only. A ``passed`` validation state means that
    the record names local evidence; it is never network consensus or trust.
    """

    if not isinstance(document, dict):
        raise CapabilityRecordError("capability record must be a JSON object")
    _require_exact_keys(
        document,
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
    if (
        not isinstance(document["schema_version"], int)
        or isinstance(document["schema_version"], bool)
        or document["schema_version"] != CAPABILITY_RECORD_SCHEMA_VERSION
    ):
        raise CapabilityRecordError("schema_version must be integer 1")
    _require_identifier(document["capability_id"], "capability_id")
    _require_identifier(document["creator_node_id"], "creator_node_id")
    _require_timestamp(document["created_at"], "created_at")
    _require_timestamp(document["updated_at"], "updated_at")
    _validate_metadata(document["metadata"])
    _validate_manifest_references(document["manifest_references"])
    _validate_validation(document["validation"])
    _validate_lineage(document["lineage"])
    _validate_attribution(
        document["contribution_attribution"], document["creator_node_id"]
    )
    return document.copy()


def _require_exact_keys(value: Any, required: set[str], field: str) -> None:
    if not isinstance(value, dict) or set(value) != required:
        raise CapabilityRecordError(f"{field} has missing or unknown fields")


def _require_identifier(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise CapabilityRecordError(f"{field} must be a safe local identifier")


def _require_timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str) or not _TIMESTAMP.fullmatch(value):
        raise CapabilityRecordError(f"{field} must be a UTC timestamp ending in Z")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise CapabilityRecordError(
            f"{field} must be a UTC timestamp ending in Z"
        ) from exc


def _require_local_reference(value: Any, field: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or value.startswith(("/", "\\"))
        or value.startswith("~")
        or "\\" in value
        or "://" in value
        or re.match(r"^[A-Za-z]:/", value) is not None
        or re.fullmatch(r"[A-Za-z0-9._/-]+", value) is None
        or ".." in value.split("/")
    ):
        raise CapabilityRecordError(f"{field} must be a safe relative local reference")


def _validate_metadata(value: Any) -> None:
    _require_exact_keys(
        value,
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
    for field in ("name", "description"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise CapabilityRecordError(f"metadata.{field} must be a non-empty string")
    if (
        not isinstance(value["capability_type"], str)
        or value["capability_type"] not in CAPABILITY_TYPES
    ):
        raise CapabilityRecordError("metadata.capability_type is unknown")
    for field in ("supported_input_formats", "supported_output_formats"):
        entries = value[field]
        if (
            not isinstance(entries, list)
            or not entries
            or not all(isinstance(entry, str) and entry.strip() for entry in entries)
        ):
            raise CapabilityRecordError(
                f"metadata.{field} must be a non-empty string list"
            )
    for field in ("constraints", "local_execution_requirements"):
        if not isinstance(value[field], list) or not all(
            isinstance(entry, str) and entry.strip() for entry in value[field]
        ):
            raise CapabilityRecordError(f"metadata.{field} must be a string list")


def _validate_manifest_references(value: Any) -> None:
    if not isinstance(value, dict) or not value:
        raise CapabilityRecordError("manifest_references must be a non-empty object")
    for kind, reference in value.items():
        if kind not in MANIFEST_KINDS:
            raise CapabilityRecordError("manifest_references contains an unknown kind")
        _require_local_reference(reference, f"manifest_references.{kind}")


def _validate_validation(value: Any) -> None:
    _require_exact_keys(
        value,
        {
            "status",
            "receipt_ids",
            "last_validated_at",
            "check_name",
            "failure_reason",
        },
        "validation",
    )
    status = value["status"]
    if not isinstance(status, str) or status not in VALIDATION_STATUSES:
        raise CapabilityRecordError("validation.status is unknown")
    receipts = value["receipt_ids"]
    if not isinstance(receipts, list) or not all(
        isinstance(receipt, str) and _RECEIPT_ID.fullmatch(receipt)
        for receipt in receipts
    ):
        raise CapabilityRecordError(
            "validation.receipt_ids contains a malformed receipt ID"
        )
    for field in ("last_validated_at", "check_name", "failure_reason"):
        if value[field] is not None and not isinstance(value[field], str):
            raise CapabilityRecordError(f"validation.{field} must be a string or null")
    if value["last_validated_at"] is not None:
        _require_timestamp(value["last_validated_at"], "validation.last_validated_at")
    if status == "passed" and (
        not receipts or not value["last_validated_at"] or not value["check_name"]
    ):
        raise CapabilityRecordError(
            "passed validation requires receipts, timestamp, and check name"
        )
    if status == "failed" and (
        not value["last_validated_at"]
        or not value["check_name"]
        or not value["failure_reason"]
    ):
        raise CapabilityRecordError(
            "failed validation requires timestamp, check name, and failure reason"
        )
    if status == "unvalidated" and any(
        (
            receipts,
            value["last_validated_at"],
            value["check_name"],
            value["failure_reason"],
        )
    ):
        raise CapabilityRecordError(
            "unvalidated capability must not claim validation evidence"
        )


def _validate_lineage(value: Any) -> None:
    _require_exact_keys(
        value,
        {
            "source_manifest_ref",
            "prior_capability_record_id",
            "local_build_artifact_ref",
        },
        "lineage",
    )
    for field in ("source_manifest_ref", "local_build_artifact_ref"):
        if value[field] is not None:
            _require_local_reference(value[field], f"lineage.{field}")
    if value["prior_capability_record_id"] is not None:
        _require_identifier(
            value["prior_capability_record_id"], "lineage.prior_capability_record_id"
        )


def _validate_attribution(value: Any, creator_node_id: str) -> None:
    _require_exact_keys(
        value,
        {"creator_node_id", "maintainer_node_id", "local_work_receipt_ids"},
        "contribution_attribution",
    )
    if value["creator_node_id"] != creator_node_id:
        raise CapabilityRecordError(
            "contribution_attribution.creator_node_id must match creator_node_id"
        )
    if value["maintainer_node_id"] is not None:
        _require_identifier(
            value["maintainer_node_id"], "contribution_attribution.maintainer_node_id"
        )
    receipts = value["local_work_receipt_ids"]
    if not isinstance(receipts, list) or not all(
        isinstance(receipt, str) and _IDENTIFIER.fullmatch(receipt)
        for receipt in receipts
    ):
        raise CapabilityRecordError(
            "contribution_attribution.local_work_receipt_ids contains a malformed receipt ID"
        )
