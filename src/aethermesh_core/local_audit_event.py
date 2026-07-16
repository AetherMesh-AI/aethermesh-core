"""Canonical local JSONL audit events for prototype actions."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import Any

AUDIT_EVENT_SCHEMA_VERSION = 1
AUDIT_EVENT_TYPES = frozenset(
    {
        "node_initialized",
        "manifest_created",
        "work_submitted",
        "job_submitted",
        "validation_attempted",
        "validation_result",
        "lineage_linked",
        "contribution_record_updated",
        "capability_advertised",
        "node.shutdown",
    }
)
_REQUIRED_FIELDS = frozenset(
    {
        "event_id",
        "timestamp",
        "event_type",
        "actor_node_id",
        "creator_node_id",
        "local_run_id",
        "schema_version",
    }
)
_OPTIONAL_FIELDS = frozenset(
    {
        "manifest_id",
        "work_id",
        "validation_receipt_id",
        "lineage_parent_ids",
        "contribution_attribution_ids",
        "related_file_paths",
        "hashes",
        "signatures",
        "node_instance_id",
        "shutdown_reason",
        "exit_mode",
        "final_lifecycle_state",
        "validation_status",
        "manifest_ref",
        "validation_receipt_ref",
        "lineage_refs",
        "contribution_attribution_refs",
        "capability_advertisement_action",
        "node_id",
        "capability_id",
        "manifest_digest",
        "advertisement_payload_digest",
        "validation_receipt_refs",
        "contribution_attribution",
        "job_id",
        "local_node_id",
        "validation_expectation",
        "attribution_metadata_hash",
    }
)


class LocalAuditEventError(ValueError):
    """Raised when a local audit event does not match the stable v1 format."""


def validate_local_audit_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return one canonical local audit event without writing it."""

    document = dict(event)
    if any(not isinstance(field, str) for field in document):
        raise LocalAuditEventError("local audit event field names must be strings")
    unknown_fields = set(document) - _REQUIRED_FIELDS - _OPTIONAL_FIELDS
    if unknown_fields:
        raise LocalAuditEventError(
            f"local audit event has unsupported fields: {', '.join(sorted(unknown_fields))}"
        )
    missing_fields = _REQUIRED_FIELDS - set(document)
    if missing_fields:
        raise LocalAuditEventError(
            f"local audit event is missing required fields: {', '.join(sorted(missing_fields))}"
        )
    if (
        not isinstance(document["schema_version"], int)
        or isinstance(document["schema_version"], bool)
        or document["schema_version"] != AUDIT_EVENT_SCHEMA_VERSION
    ):
        raise LocalAuditEventError("local audit event.schema_version must be integer 1")
    for field in ("event_id", "actor_node_id", "local_run_id"):
        _require_text(document[field], f"local audit event.{field}")
    _require_timestamp(document["timestamp"])
    creator_node_id = document["creator_node_id"]
    if creator_node_id is not None:
        _require_text(creator_node_id, "local audit event.creator_node_id")
    if (
        not isinstance(document["event_type"], str)
        or document["event_type"] not in AUDIT_EVENT_TYPES
    ):
        raise LocalAuditEventError("local audit event.event_type is unsupported")
    for field in ("manifest_id", "work_id", "validation_receipt_id"):
        if field in document:
            _require_text(document[field], f"local audit event.{field}")
    for field in ("lineage_parent_ids", "contribution_attribution_ids"):
        if field in document:
            _require_text_list(document[field], f"local audit event.{field}")
    for field in ("lineage_refs", "contribution_attribution_refs"):
        if field in document:
            _require_local_paths(document[field], f"local audit event.{field}")
    for field in (
        "node_instance_id",
        "exit_mode",
        "final_lifecycle_state",
        "validation_status",
    ):
        if field in document:
            _require_text(document[field], f"local audit event.{field}")
    for field in ("shutdown_reason", "manifest_ref", "validation_receipt_ref"):
        if field in document and document[field] is not None:
            _require_text(document[field], f"local audit event.{field}")
    for field in ("manifest_ref", "validation_receipt_ref"):
        if field in document and document[field] is not None:
            _require_local_paths([document[field]], f"local audit event.{field}")
    if "related_file_paths" in document:
        _require_local_paths(
            document["related_file_paths"], "local audit event.related_file_paths"
        )
    for field in ("hashes", "signatures"):
        if field in document:
            _require_text_mapping(document[field], f"local audit event.{field}")
    if document["event_type"] == "node.shutdown":
        _validate_shutdown_event(document)
    if document["event_type"] == "capability_advertised":
        _validate_capability_advertisement_event(document)
    if document["event_type"] == "job_submitted":
        _validate_job_submission_event(document)
    return document


def append_local_audit_event(
    path: str | Path, event: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate and append one event; this API never updates prior JSONL records."""

    document = validate_local_audit_event(event)
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return document


def _require_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LocalAuditEventError(f"{label} must be a non-empty string")


def _require_timestamp(value: object) -> None:
    if not isinstance(value, str):
        raise LocalAuditEventError(
            "local audit event.timestamp must be a UTC timestamp"
        )
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise LocalAuditEventError(
            "local audit event.timestamp must be a UTC timestamp"
        ) from exc


def _require_text_list(value: object, label: str) -> None:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise LocalAuditEventError(f"{label} must be a list of non-empty strings")


def _require_local_paths(value: object, label: str) -> None:
    if not isinstance(value, list):
        raise LocalAuditEventError(f"{label} must be a list of non-empty strings")
    _require_text_list(value, label)
    for item in value:
        path_variants = (Path(item), PureWindowsPath(item))
        has_parent_reference = any(".." in path.parts for path in path_variants)
        is_absolute = any(path.is_absolute() for path in path_variants)
        if (
            is_absolute
            or has_parent_reference
            or item.startswith("~")
            or "://" in item
            or "\\" in item
        ):
            raise LocalAuditEventError(f"{label} must contain safe relative paths")


def _require_text_mapping(value: object, label: str) -> None:
    if not isinstance(value, dict) or any(
        not isinstance(key, str)
        or not key.strip()
        or not isinstance(item, str)
        or not item.strip()
        for key, item in value.items()
    ):
        raise LocalAuditEventError(f"{label} must be an object of non-empty strings")


def _validate_shutdown_event(document: Mapping[str, Any]) -> None:
    """Require explicit local context for durable node shutdown audit entries."""

    required_fields = (
        "node_instance_id",
        "shutdown_reason",
        "exit_mode",
        "final_lifecycle_state",
        "validation_status",
        "manifest_ref",
        "validation_receipt_ref",
        "lineage_refs",
        "contribution_attribution_refs",
    )
    missing = [field for field in required_fields if field not in document]
    if missing:
        raise LocalAuditEventError(
            f"node.shutdown event is missing required context: {', '.join(missing)}"
        )
    _require_text(document["creator_node_id"], "node.shutdown.creator_node_id")


def _validate_capability_advertisement_event(document: Mapping[str, Any]) -> None:
    """Require compact provenance for one local capability advertisement."""

    required_fields = (
        "capability_advertisement_action",
        "node_id",
        "capability_id",
        "manifest_ref",
        "manifest_digest",
        "advertisement_payload_digest",
        "validation_status",
        "validation_receipt_refs",
        "lineage_refs",
        "contribution_attribution",
    )
    missing = [field for field in required_fields if field not in document]
    if missing:
        raise LocalAuditEventError(
            "capability_advertised event is missing required context: "
            f"{', '.join(missing)}"
        )
    if document["capability_advertisement_action"] not in {
        "created",
        "refreshed",
        "replaced",
    }:
        raise LocalAuditEventError(
            "capability_advertised action must be created, refreshed, or replaced"
        )
    for field in (
        "node_id",
        "capability_id",
        "manifest_digest",
        "advertisement_payload_digest",
        "validation_status",
    ):
        _require_text(document[field], f"capability_advertised.{field}")
    _require_text(document["creator_node_id"], "capability_advertised.creator_node_id")
    _require_local_paths(
        document["validation_receipt_refs"],
        "capability_advertised.validation_receipt_refs",
    )
    _require_text_mapping(
        document["contribution_attribution"],
        "capability_advertised.contribution_attribution",
    )


def _validate_job_submission_event(document: Mapping[str, Any]) -> None:
    """Require compact, non-payload evidence for one accepted local submission."""

    required_fields = (
        "job_id",
        "local_node_id",
        "manifest_ref",
        "hashes",
        "lineage_refs",
        "validation_expectation",
        "contribution_attribution",
        "attribution_metadata_hash",
    )
    missing = [field for field in required_fields if field not in document]
    if missing:
        raise LocalAuditEventError(
            f"job_submitted event is missing required context: {', '.join(missing)}"
        )
    for field in (
        "job_id",
        "local_node_id",
        "validation_expectation",
        "attribution_metadata_hash",
    ):
        _require_text(document[field], f"job_submitted.{field}")
    if document["actor_node_id"] != document["local_node_id"]:
        raise LocalAuditEventError(
            "job_submitted.local_node_id must match actor_node_id"
        )
    _require_text(document["creator_node_id"], "job_submitted.creator_node_id")
    _require_text_mapping(
        document["contribution_attribution"], "job_submitted.contribution_attribution"
    )
