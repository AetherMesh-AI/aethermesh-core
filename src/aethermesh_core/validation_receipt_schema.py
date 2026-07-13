"""Schema validation and stable hashing for local validation receipts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

VALIDATION_RECEIPT_SCHEMA_VERSION = 1
VALIDATION_STATUSES = frozenset({"pass", "fail", "error", "skipped"})
_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "receipt_id",
        "receipt_hash",
        "created_at",
        "creator_node_id",
        "work_id",
        "manifest_id",
        "validation_status",
        "validator_id",
        "lineage",
        "contribution",
        "evidence",
    }
)
_LINEAGE_FIELDS = frozenset(
    {
        "parent_work_ids",
        "source_manifest_refs",
        "input_hashes",
        "output_hashes",
        "prior_receipt_ids",
    }
)
_CONTRIBUTION_FIELDS = frozenset(
    {"submitter_id", "local_node_id", "claimed_role", "contribution_manifest_ref"}
)
_EVIDENCE_FIELDS = frozenset(
    {
        "test_command",
        "environment_summary",
        "exit_code",
        "log_path",
        "artifact_path",
        "reason",
    }
)


class ValidationReceiptSchemaError(ValueError):
    """Raised when a local validation receipt violates its stable schema."""


def canonical_validation_receipt_hash(document: object) -> str:
    """Hash stable receipt evidence, excluding local creation time and hash itself."""

    if not isinstance(document, dict):
        raise ValidationReceiptSchemaError("validation receipt must be an object")
    payload = {
        key: value
        for key, value in document.items()
        if key not in {"created_at", "receipt_hash"}
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_validation_receipt_document(document: object) -> dict[str, Any]:
    """Validate one JSON-only local receipt without filesystem access."""

    receipt = _object(document, "validation receipt", _REQUIRED_FIELDS)
    if receipt["schema_version"] != VALIDATION_RECEIPT_SCHEMA_VERSION or isinstance(
        receipt["schema_version"], bool
    ):
        raise ValidationReceiptSchemaError(
            "validation receipt.schema_version must be integer 1"
        )
    for field in (
        "receipt_id",
        "creator_node_id",
        "work_id",
        "manifest_id",
        "validator_id",
    ):
        _identifier(receipt[field], f"validation receipt.{field}")
    _timestamp(receipt["created_at"], "validation receipt.created_at")
    if receipt["validation_status"] not in VALIDATION_STATUSES:
        raise ValidationReceiptSchemaError(
            "validation receipt.validation_status is unsupported"
        )
    _lineage(receipt["lineage"])
    _contribution(receipt["contribution"])
    _evidence(receipt["evidence"])
    if not isinstance(receipt["receipt_hash"], str) or receipt[
        "receipt_hash"
    ] != canonical_validation_receipt_hash(receipt):
        raise ValidationReceiptSchemaError(
            "validation receipt.receipt_hash does not match"
        )
    return receipt


def _object(value: object, label: str, required: frozenset[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationReceiptSchemaError(f"{label} must be an object")
    fields = set(value)
    missing = sorted(required - fields)
    if missing:
        raise ValidationReceiptSchemaError(f"{label} missing: {', '.join(missing)}")
    unknown = sorted(fields - required)
    if unknown:
        raise ValidationReceiptSchemaError(
            f"{label} contains unsupported fields: {', '.join(unknown)}"
        )
    return value


def _identifier(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value.strip() != value
        or any(character.isspace() for character in value)
    ):
        raise ValidationReceiptSchemaError(f"{label} must be a non-empty identifier")


def _timestamp(value: object, label: str) -> None:
    if not isinstance(value, str):
        raise ValidationReceiptSchemaError(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationReceiptSchemaError(f"{label} must be a UTC timestamp") from exc
    if parsed.tzinfo != UTC:
        raise ValidationReceiptSchemaError(f"{label} must be a UTC timestamp")


def _string_list(value: object, label: str) -> None:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item and item.strip() == item for item in value
    ):
        raise ValidationReceiptSchemaError(f"{label} must be a string list")


def _nullable_string(value: object, label: str) -> None:
    if value is not None and (
        not isinstance(value, str) or not value or value.strip() != value
    ):
        raise ValidationReceiptSchemaError(
            f"{label} must be null or a non-empty string"
        )


def _lineage(value: object) -> None:
    lineage = _object(value, "validation receipt.lineage", _LINEAGE_FIELDS)
    for field in _LINEAGE_FIELDS:
        _string_list(lineage[field], f"validation receipt.lineage.{field}")


def _contribution(value: object) -> None:
    contribution = _object(
        value, "validation receipt.contribution", _CONTRIBUTION_FIELDS
    )
    for field in _CONTRIBUTION_FIELDS:
        _nullable_string(
            contribution[field], f"validation receipt.contribution.{field}"
        )


def _evidence(value: object) -> None:
    evidence = _object(value, "validation receipt.evidence", _EVIDENCE_FIELDS)
    for field in ("test_command", "environment_summary", "log_path", "artifact_path"):
        _nullable_string(evidence[field], f"validation receipt.evidence.{field}")
    _nullable_string(evidence["reason"], "validation receipt.evidence.reason")
    exit_code = evidence["exit_code"]
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        raise ValidationReceiptSchemaError(
            "validation receipt.evidence.exit_code must be null or an integer"
        )
