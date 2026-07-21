"""Small, local-only version 1 model/expert manifest validation."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, cast

MANIFEST_SCHEMA_VERSION = 1
RECEIPT_VERSION = "aethermesh-expert-validation-receipt/v0"
_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SAFE_REFERENCE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*\Z")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_STATUSES = {"unvalidated", "passed", "failed"}
_TOP_LEVEL = {
    "version",
    "model_id",
    "expert_id",
    "name",
    "creator_node_id",
    "created_at",
    "artifact",
    "supported_task_categories",
    "runtime_requirements",
    "lineage",
    "validation",
    "contribution_attribution",
}
_REQUIRED_TOP_LEVEL = _TOP_LEVEL - {"model_id", "expert_id"}


class ExpertManifestError(ValueError):
    """Raised when a local expert manifest is incomplete or malformed."""


def load_expert_manifest(path: str | Path) -> dict[str, Any]:
    """Load and structurally validate one hand-authored version 1 expert manifest."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ExpertManifestError("could not read expert manifest") from exc
    except UnicodeDecodeError as exc:
        raise ExpertManifestError(
            "expert manifest JSON is malformed: invalid UTF-8"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ExpertManifestError(
            f"expert manifest JSON is malformed: {exc.msg}"
        ) from exc
    validate_expert_manifest(document)
    return cast(dict[str, Any], document)


def validate_expert_manifest(document: object) -> None:
    """Validate required version 1 fields without claiming network trust or capability."""
    document = _top_level_object(document)
    _manifest_version(document["version"])
    _identity(document)
    for field in ("creator_node_id", "created_at"):
        _string(document[field], field)
    _text(document["name"], "name")
    _timestamp(document["created_at"], "created_at")
    _artifact(document["artifact"])
    _strings(document["supported_task_categories"], "supported_task_categories", True)
    _strings(document["runtime_requirements"], "runtime_requirements", True)
    _lineage(document["lineage"])
    _validation(document["validation"])
    _attribution(document["contribution_attribution"], document["creator_node_id"])
    _consistent_validation_attribution(document)


def expert_is_usable(path: str | Path) -> bool:
    """Require passed validation plus matching local artifact and receipt evidence."""
    manifest_path = Path(path)
    document = load_expert_manifest(manifest_path)
    validation = _object(document["validation"], _VALIDATION, "validation")
    if validation["status"] != "passed":
        return False
    artifact = _object(document["artifact"], {"reference", "sha256"}, "artifact")
    try:
        artifact_path = _local_reference_path(
            manifest_path.parent, str(artifact["reference"])
        )
        receipt_path = _local_reference_path(
            manifest_path.parent, str(validation["receipt_path"])
        )
        return (
            artifact_path.is_file()
            and _sha256(artifact_path) == artifact["sha256"]
            and _receipt_matches_manifest(receipt_path, document)
        )
    except OSError:
        return False


def _receipt_matches_manifest(path: Path, document: dict[str, Any]) -> bool:
    """Reject a self-asserted pass unless its receipt binds the validated artifact."""
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(receipt, dict):
        return False
    validation = cast(dict[str, Any], document["validation"])
    return receipt == {
        "receipt_version": RECEIPT_VERSION,
        "name": document["name"],
        **{field: document[field] for field in _identity_fields(document)},
        "creator_node_id": document["creator_node_id"],
        "created_at": document["created_at"],
        "artifact_sha256": cast(dict[str, Any], document["artifact"])["sha256"],
        "validated_at": validation["last_validated_at"],
        "validator_node_id": validation["validator_node_id"],
        "status": "passed",
    }


def _object(value: object, keys: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        listed = ", ".join(sorted(keys))
        raise ExpertManifestError(f"{context} must contain exactly: {listed}")
    return cast(dict[str, Any], value)


def _top_level_object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExpertManifestError("expert manifest must be a JSON object")
    fields = set(value)
    missing = _REQUIRED_TOP_LEVEL - fields
    if missing:
        raise ExpertManifestError(
            "expert manifest is missing required field(s): "
            + ", ".join(sorted(missing))
        )
    if not fields <= _TOP_LEVEL:
        listed = ", ".join(sorted(_TOP_LEVEL))
        raise ExpertManifestError(
            f"expert manifest must contain exactly these allowed fields: {listed}"
        )
    return cast(dict[str, Any], value)


def _identity(document: dict[str, Any]) -> None:
    fields = _identity_fields(document)
    if not any(
        isinstance(document[field], str) and document[field].strip() for field in fields
    ):
        raise ExpertManifestError(
            "expert manifest requires at least one non-empty model_id or expert_id"
        )
    for field in fields:
        _string(document[field], field)


def _identity_fields(document: dict[str, Any]) -> set[str]:
    return {field for field in ("model_id", "expert_id") if field in document}


def _manifest_version(value: object) -> None:
    if type(value) is not int or value != MANIFEST_SCHEMA_VERSION:
        raise ExpertManifestError(
            f"version must be {MANIFEST_SCHEMA_VERSION} (the integer for this manifest format)"
        )


def _string(value: object, context: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(char.isspace() for char in value)
    ):
        raise ExpertManifestError(
            f"{context} must be a non-empty whitespace-free string"
        )


def _text(value: object, context: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExpertManifestError(f"{context} must be a non-empty string")


def _timestamp(value: object, context: str) -> None:
    _string(value, context)
    timestamp = cast(str, value)
    if not _TIMESTAMP.fullmatch(timestamp):
        raise ExpertManifestError(f"{context} must be a UTC timestamp ending in Z")
    try:
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ExpertManifestError(
            f"{context} must be a UTC timestamp ending in Z"
        ) from exc


def _reference(value: object, context: str) -> None:
    _string(value, context)
    reference = cast(str, value)
    if (
        not _SAFE_REFERENCE.fullmatch(reference)
        or "/../" in f"/{reference}"
        or reference.startswith("/")
    ):
        raise ExpertManifestError(f"{context} must be a safe local relative reference")


def _strings(value: object, context: str, required: bool = False) -> None:
    if not isinstance(value, list) or (required and not value):
        raise ExpertManifestError(
            f"{context} must be a non-empty list of non-empty strings"
        )
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ExpertManifestError(f"{context} must be a list of non-empty strings")


def _nullable_reference(value: object, context: str) -> None:
    if value is not None:
        _reference(value, context)


def _artifact(value: object) -> None:
    value = _object(value, {"reference", "sha256"}, "artifact")
    _reference(value["reference"], "artifact.reference")
    if not isinstance(value["sha256"], str) or not _HASH.fullmatch(value["sha256"]):
        raise ExpertManifestError(
            "artifact.sha256 must be a lowercase sha256 content hash"
        )


def _lineage(value: object) -> None:
    value = _object(value, _LINEAGE, "lineage")
    _string(value["source_model"], "lineage.source_model")
    _nullable_reference(value["adapter_ref"], "lineage.adapter_ref")
    _nullable_reference(value["prompt_template_ref"], "lineage.prompt_template_ref")
    if not isinstance(value["local_changes"], str):
        raise ExpertManifestError("lineage.local_changes must be a string")
    _strings(value["parent_manifest_ids"], "lineage.parent_manifest_ids")
    _strings(value["derived_artifact_refs"], "lineage.derived_artifact_refs")
    for item in value["derived_artifact_refs"]:
        _reference(item, "lineage.derived_artifact_refs item")


_VALIDATION = {
    "test_command",
    "expected_inputs_ref",
    "receipt_path",
    "last_validated_at",
    "status",
    "validator_node_id",
}
_LINEAGE = {
    "source_model",
    "adapter_ref",
    "prompt_template_ref",
    "local_changes",
    "parent_manifest_ids",
    "derived_artifact_refs",
}


def _validation(value: object) -> None:
    value = _object(value, _VALIDATION, "validation")
    if not isinstance(value["status"], str) or value["status"] not in _STATUSES:
        raise ExpertManifestError(
            "validation.status must be unvalidated, passed, or failed"
        )
    for field in ("expected_inputs_ref", "receipt_path"):
        _nullable_reference(value[field], f"validation.{field}")
    for field in ("test_command", "validator_node_id"):
        if value[field] is not None:
            _text(value[field], f"validation.{field}")
    if value["last_validated_at"] is not None:
        _timestamp(value["last_validated_at"], "validation.last_validated_at")
    if value["status"] == "passed" and any(
        value[field] is None for field in _VALIDATION - {"status"}
    ):
        raise ExpertManifestError("passed validation requires complete local evidence")


def _attribution(value: object, creator_node_id: object) -> None:
    value = _object(
        value,
        {"creator_node_id", "modifier_node_ids", "validator_node_id", "receipt_refs"},
        "contribution_attribution",
    )
    if value["creator_node_id"] != creator_node_id:
        raise ExpertManifestError(
            "contribution_attribution.creator_node_id must match creator_node_id"
        )
    _strings(value["modifier_node_ids"], "contribution_attribution.modifier_node_ids")
    if value["validator_node_id"] is not None:
        _string(
            value["validator_node_id"], "contribution_attribution.validator_node_id"
        )
    _strings(value["receipt_refs"], "contribution_attribution.receipt_refs")
    for item in value["receipt_refs"]:
        _reference(item, "contribution_attribution.receipt_refs item")


def _consistent_validation_attribution(document: dict[str, Any]) -> None:
    validation = cast(dict[str, Any], document["validation"])
    attribution = cast(dict[str, Any], document["contribution_attribution"])
    if attribution["validator_node_id"] != validation["validator_node_id"]:
        raise ExpertManifestError(
            "contribution validator_node_id must match validation.validator_node_id"
        )
    receipt_path = validation["receipt_path"]
    if receipt_path is not None and receipt_path not in attribution["receipt_refs"]:
        raise ExpertManifestError(
            "validation.receipt_path must appear in contribution receipt_refs"
        )


def _local_reference_path(root: Path, reference: str) -> Path:
    resolved_root = root.resolve()
    path = (resolved_root / reference).resolve()
    if resolved_root != path and resolved_root not in path.parents:
        raise OSError("local reference escapes manifest directory")
    return path


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
