"""Locally observable software and runtime version metadata."""

from __future__ import annotations

import os
import platform
import re
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from importlib import metadata

VERSION_METADATA_SCHEMA_VERSION = 1
DEFAULT_BUILD_IDENTIFIER = "local-build-unset"
REQUIRED_VERSION_METADATA_FIELDS = frozenset(
    {
        "version_metadata_schema_version",
        "node_software_version",
        "build_identifier",
        "runtime_name",
        "runtime_version",
        "operating_system",
        "architecture",
        "manifest_schema_version",
        "validation_schema_version",
        "captured_at",
    }
)
BUILD_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")


class VersionMetadataError(ValueError):
    """Raised when local version metadata is missing or malformed."""


def capture_version_metadata(*, captured_at: str | None = None) -> dict[str, object]:
    """Return factual local software/runtime metadata for one node run."""

    timestamp = captured_at or datetime.now(UTC).replace(microsecond=0).isoformat()
    document: dict[str, object] = {
        "version_metadata_schema_version": VERSION_METADATA_SCHEMA_VERSION,
        "node_software_version": _node_software_version(),
        "build_identifier": os.environ.get(
            "AETHERMESH_BUILD_ID", DEFAULT_BUILD_IDENTIFIER
        ),
        "runtime_name": platform.python_implementation(),
        "runtime_version": platform.python_version(),
        "operating_system": platform.system(),
        "architecture": platform.machine(),
        "manifest_schema_version": 1,
        "validation_schema_version": 1,
        "captured_at": timestamp,
    }
    validate_version_metadata(document)
    return document


def validate_version_metadata(document: object) -> dict[str, object]:
    """Validate and return a shallow copy of a version metadata document."""

    if not isinstance(document, dict):
        raise VersionMetadataError("version metadata must be a JSON object")
    missing_fields = sorted(REQUIRED_VERSION_METADATA_FIELDS - document.keys())
    if missing_fields:
        raise VersionMetadataError(
            "version metadata missing required fields: " + ", ".join(missing_fields)
        )
    unknown_fields = sorted(document.keys() - REQUIRED_VERSION_METADATA_FIELDS)
    if unknown_fields:
        raise VersionMetadataError(
            "version metadata contains unsupported fields: " + ", ".join(unknown_fields)
        )
    schema_version = document["version_metadata_schema_version"]
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != VERSION_METADATA_SCHEMA_VERSION
    ):
        raise VersionMetadataError(
            "version metadata field 'version_metadata_schema_version' must be integer 1"
        )
    for field_name in (
        "node_software_version",
        "build_identifier",
        "runtime_name",
        "runtime_version",
        "operating_system",
        "architecture",
    ):
        _require_non_empty_string(document, field_name)
    build_identifier = str(document["build_identifier"])
    if BUILD_IDENTIFIER_PATTERN.fullmatch(build_identifier) is None:
        raise VersionMetadataError(
            "version metadata field 'build_identifier' must be reference-safe"
        )
    for field_name in ("manifest_schema_version", "validation_schema_version"):
        value = document[field_name]
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise VersionMetadataError(
                f"version metadata field '{field_name}' must be a positive integer"
            )
    _require_utc_timestamp(_require_non_empty_string(document, "captured_at"))
    return dict(document)


def version_metadata_ref(document: object) -> str:
    """Return a stable local reference for one validated metadata document."""

    metadata_document = validate_version_metadata(document)
    encoded = repr(sorted(metadata_document.items())).encode("utf-8")
    return "version-metadata-sha256:" + sha256(encoded).hexdigest()


def _node_software_version() -> str:
    try:
        return metadata.version("aethermesh")
    except metadata.PackageNotFoundError:
        from aethermesh_core import __version__

        return __version__


def _require_non_empty_string(document: dict[str, object], field_name: str) -> str:
    value = document[field_name]
    if not isinstance(value, str) or not value.strip():
        raise VersionMetadataError(
            f"version metadata field '{field_name}' must be a non-empty string"
        )
    return value


def _require_utc_timestamp(value: str) -> None:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise VersionMetadataError(
            "version metadata field 'captured_at' must be an ISO 8601 timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise VersionMetadataError(
            "version metadata field 'captured_at' must include a timezone"
        )
    if parsed.utcoffset() != timedelta(0):
        raise VersionMetadataError(
            "version metadata field 'captured_at' must be a UTC timestamp"
        )
