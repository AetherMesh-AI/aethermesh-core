"""Canonical local JSONL audit events for prototype actions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

AUDIT_EVENT_SCHEMA_VERSION = 1
AUDIT_EVENT_TYPES = frozenset(
    {
        "node_initialized",
        "manifest_created",
        "work_submitted",
        "validation_attempted",
        "validation_result",
        "lineage_linked",
        "contribution_record_updated",
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
    }
)


class LocalAuditEventError(ValueError):
    """Raised when a local audit event does not match the stable v1 format."""


def validate_local_audit_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return one canonical local audit event without writing it."""

    document = dict(event)
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
    if document["schema_version"] != AUDIT_EVENT_SCHEMA_VERSION:
        raise LocalAuditEventError("local audit event.schema_version must be integer 1")
    for field in ("event_id", "timestamp", "actor_node_id", "local_run_id"):
        _require_text(document[field], f"local audit event.{field}")
    creator_node_id = document["creator_node_id"]
    if creator_node_id is not None:
        _require_text(creator_node_id, "local audit event.creator_node_id")
    if document["event_type"] not in AUDIT_EVENT_TYPES:
        raise LocalAuditEventError("local audit event.event_type is unsupported")
    for field in ("manifest_id", "work_id", "validation_receipt_id"):
        if field in document:
            _require_text(document[field], f"local audit event.{field}")
    for field in ("lineage_parent_ids", "contribution_attribution_ids"):
        if field in document:
            _require_text_list(document[field], f"local audit event.{field}")
    if "related_file_paths" in document:
        _require_local_paths(document["related_file_paths"])
    for field in ("hashes", "signatures"):
        if field in document:
            _require_text_mapping(document[field], f"local audit event.{field}")
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
    return document


def _require_text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LocalAuditEventError(f"{label} must be a non-empty string")


def _require_text_list(value: object, label: str) -> None:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise LocalAuditEventError(f"{label} must be a list of non-empty strings")


def _require_local_paths(value: object) -> None:
    if not isinstance(value, list):
        raise LocalAuditEventError(
            "local audit event.related_file_paths must be a list of non-empty strings"
        )
    _require_text_list(value, "local audit event.related_file_paths")
    for item in value:
        path = Path(item)
        if path.is_absolute() or ".." in path.parts:
            raise LocalAuditEventError(
                "local audit event.related_file_paths must be safe relative paths"
            )


def _require_text_mapping(value: object, label: str) -> None:
    if not isinstance(value, dict) or any(
        not isinstance(key, str)
        or not key.strip()
        or not isinstance(item, str)
        or not item.strip()
        for key, item in value.items()
    ):
        raise LocalAuditEventError(f"{label} must be an object of non-empty strings")
