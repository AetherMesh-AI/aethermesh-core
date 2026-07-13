"""Schema validation and stable hashing for local validation receipts."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

VALIDATION_RECEIPT_SCHEMA_VERSION = 1
VALIDATION_STATUSES = frozenset({"pass", "fail", "error", "skipped"})
VALIDATION_RECEIPT_ID_PREFIX = "local-validation-receipt-"
_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "receipt_id",
        "receipt_hash",
        "result_hash",
        "created_at",
        "creator_node_id",
        "job_id",
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


def validation_receipt_id(work_id: str) -> str:
    """Return the stable local receipt identifier for one work item."""

    _identifier(work_id, "validation receipt.work_id")
    return f"{VALIDATION_RECEIPT_ID_PREFIX}{work_id}"


def canonical_validation_receipt_hash(document: object) -> str:
    """Hash stable receipt evidence, excluding local creation time and hash itself."""

    if not isinstance(document, dict):
        raise ValidationReceiptSchemaError("validation receipt must be an object")
    payload = {
        key: value
        for key, value in document.items()
        if key not in {"created_at", "receipt_hash"}
    }
    try:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValidationReceiptSchemaError(
            "validation receipt must contain JSON-compatible data"
        ) from exc
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_validation_receipt_document(document: object) -> dict[str, Any]:
    """Validate one JSON-only local receipt without filesystem access."""

    receipt = _object(document, "validation receipt", _REQUIRED_FIELDS)
    if (
        not isinstance(receipt["schema_version"], int)
        or isinstance(receipt["schema_version"], bool)
        or receipt["schema_version"] != VALIDATION_RECEIPT_SCHEMA_VERSION
    ):
        raise ValidationReceiptSchemaError(
            "validation receipt.schema_version must be integer 1"
        )
    for field in (
        "receipt_id",
        "creator_node_id",
        "job_id",
        "work_id",
        "manifest_id",
        "validator_id",
    ):
        _identifier(receipt[field], f"validation receipt.{field}")
    if receipt["receipt_id"] != validation_receipt_id(receipt["work_id"]):
        raise ValidationReceiptSchemaError(
            "validation receipt.receipt_id must match its work_id"
        )
    if receipt["job_id"] != receipt["work_id"]:
        raise ValidationReceiptSchemaError(
            "validation receipt.job_id must match its work_id"
        )
    _content_addressed_id(receipt["manifest_id"], "validation receipt.manifest_id")
    _sha256_digest(receipt["result_hash"], "validation receipt.result_hash")
    _timestamp(receipt["created_at"], "validation receipt.created_at")
    if (
        not isinstance(receipt["validation_status"], str)
        or receipt["validation_status"] not in VALIDATION_STATUSES
    ):
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


def _content_addressed_id(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
    ):
        raise ValidationReceiptSchemaError(
            f"{label} must be a SHA-256 content-addressed ID"
        )


def _sha256_digest(value: object, label: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValidationReceiptSchemaError(
            f"{label} must be a lowercase SHA-256 digest"
        )


def _local_reference(value: object, label: str, *, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValidationReceiptSchemaError(
            f"{label} must be a safe relative local path"
        )
    if (
        value.startswith(("/", "~"))
        or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", value) is not None
        or "\\" in value
        or any(part == ".." for part in value.split("/"))
    ):
        raise ValidationReceiptSchemaError(
            f"{label} must be a safe relative local path"
        )


def _nullable_string(value: object, label: str) -> None:
    if value is not None and (
        not isinstance(value, str) or not value or value.strip() != value
    ):
        raise ValidationReceiptSchemaError(
            f"{label} must be null or a non-empty string"
        )


def _nullable_identifier(value: object, label: str) -> None:
    if value is not None:
        _identifier(value, label)


def _lineage(value: object) -> None:
    lineage = _object(value, "validation receipt.lineage", _LINEAGE_FIELDS)
    for field in ("parent_work_ids", "prior_receipt_ids"):
        _string_list(lineage[field], f"validation receipt.lineage.{field}")
        for identifier in lineage[field]:
            _identifier(identifier, f"validation receipt.lineage.{field} entries")
    _string_list(
        lineage["source_manifest_refs"],
        "validation receipt.lineage.source_manifest_refs",
    )
    for reference in lineage["source_manifest_refs"]:
        _local_reference(
            reference, "validation receipt.lineage.source_manifest_refs entries"
        )
    for field in ("input_hashes", "output_hashes"):
        _string_list(lineage[field], f"validation receipt.lineage.{field}")
        for content_hash in lineage[field]:
            _content_addressed_id(
                content_hash, f"validation receipt.lineage.{field} entries"
            )


def _contribution(value: object) -> None:
    contribution = _object(
        value, "validation receipt.contribution", _CONTRIBUTION_FIELDS
    )
    for field in ("submitter_id", "local_node_id", "claimed_role"):
        _nullable_identifier(
            contribution[field], f"validation receipt.contribution.{field}"
        )
    _local_reference(
        contribution["contribution_manifest_ref"],
        "validation receipt.contribution.contribution_manifest_ref",
        nullable=True,
    )


def _evidence(value: object) -> None:
    evidence = _object(value, "validation receipt.evidence", _EVIDENCE_FIELDS)
    for field in ("test_command", "environment_summary", "log_path", "artifact_path"):
        _nullable_string(evidence[field], f"validation receipt.evidence.{field}")
    for field in ("log_path", "artifact_path"):
        _local_reference(
            evidence[field], f"validation receipt.evidence.{field}", nullable=True
        )
    if not isinstance(evidence["reason"], str) or not evidence["reason"].strip():
        raise ValidationReceiptSchemaError(
            "validation receipt.evidence.reason must be a non-empty string"
        )
    exit_code = evidence["exit_code"]
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        raise ValidationReceiptSchemaError(
            "validation receipt.evidence.exit_code must be null or an integer"
        )
