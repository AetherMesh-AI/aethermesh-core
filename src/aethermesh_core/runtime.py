"""Explicit local node runtime API shared by CLI and tests.

This module is the boundary for local node lifecycle orchestration. Functions here
return structured objects/documents and never print; command-line handlers are
responsible only for parsing arguments, formatting results, and exit codes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethermesh_core.local_json_helpers import load_json_mapping
from aethermesh_core.local_runtime_config import (
    DEFAULT_RUNTIME_PATHS,
    LOCAL_RUNTIME_CONFIG_PATH,
    LocalRuntimeConfig,
    LocalRuntimeConfigError,
    load_local_runtime_config,
)
from aethermesh_core.local_restart import LocalRestartError, LocalRestartResult
from aethermesh_core.local_restart import restart_local_node as _restart_local_node
from aethermesh_core.local_shutdown import LocalShutdownError, LocalShutdownResult
from aethermesh_core.local_shutdown import shutdown_local_node as _shutdown_local_node
from aethermesh_core.local_startup import LocalStartupError, LocalStartupResult
from aethermesh_core.local_startup import start_local_node as _start_local_node
from aethermesh_core.local_validation import LocalValidationError
from aethermesh_core.local_validation import (
    validate_local_results as _validate_local_results,
)


class LocalRuntimeInspectError(ValueError):
    """Raised when persisted local runtime artifacts cannot be inspected."""


def start_local_node_runtime(
    runtime_dir: str | Path, *, reset_creator_identity: bool = False
) -> LocalStartupResult:
    """Start/initialize one local node runtime and return startup artifacts."""

    return _start_local_node(runtime_dir, reset_creator_identity=reset_creator_identity)


def stop_local_node_runtime(
    runtime_dir: str | Path, *, timeout_seconds: float = 5.0
) -> LocalShutdownResult:
    """Stop one local node runtime and return persisted shutdown state."""

    return _shutdown_local_node(runtime_dir, timeout_seconds=timeout_seconds)


def restart_local_node_runtime(
    runtime_dir: str | Path, *, timeout_seconds: float = 5.0
) -> LocalRestartResult:
    """Restart one local node runtime without changing node identity."""

    return _restart_local_node(runtime_dir, timeout_seconds=timeout_seconds)


def validate_local_node_results(
    *,
    assignment_log_path: str | Path,
    result_log_path: str | Path,
    validation_log_path: str | Path,
) -> dict[str, object]:
    """Validate local result messages and persist structured validation output."""

    return _validate_local_results(
        assignment_log_path=assignment_log_path,
        result_log_path=result_log_path,
        validation_log_path=validation_log_path,
    )


def inspect_local_node_runtime(runtime_dir: str | Path) -> dict[str, object]:
    """Inspect local identity, manifest, receipt, lineage, and attribution refs."""

    root = Path(runtime_dir)
    config = _load_runtime_config(root)
    identity_path = _configured_path(root, config, "identity")
    manifest_path = _configured_path(root, config, "manifest")
    identity = _load_runtime_json(identity_path, "identity")
    manifest = _load_runtime_json(manifest_path, "manifest")
    node = _required_mapping(identity, "node", "identity")
    manifest_node = _required_mapping(manifest, "node", "manifest")
    node_id = _required_text(node, "node_id", "identity.node")
    creator_node_id = _required_text(node, "creator_node_id", "identity.node")
    manifest_node_id = _required_text(manifest_node, "node_id", "manifest.node")
    manifest_creator_node_id = _required_text(
        manifest_node, "creator_node_id", "manifest.node"
    )
    references = identity.get("references")
    lineage = identity.get("lineage")
    attribution = identity.get("contribution_attribution")
    if not isinstance(references, dict):
        raise LocalRuntimeInspectError("identity references must be an object")
    if not isinstance(lineage, dict):
        raise LocalRuntimeInspectError("identity lineage must be an object")
    if not isinstance(attribution, dict):
        raise LocalRuntimeInspectError(
            "identity contribution_attribution must be an object"
        )

    receipt_refs = _artifact_refs(root, _configured_ref(config, "validation_receipts"))
    lineage_refs = _artifact_refs(root, _configured_ref(config, "lineage"))
    contribution_refs = _artifact_refs(
        root, _configured_ref(config, "contribution_attribution")
    )
    return {
        "node_id": node_id,
        "creator_node_id": creator_node_id,
        "identity_path": _relative_ref(root, identity_path),
        "manifest_path": _relative_ref(root, manifest_path),
        "manifest_matches_identity": manifest_node_id == node_id
        and manifest_creator_node_id == creator_node_id,
        "manifest_refs": _string_list(references.get("manifest_refs")),
        "validation_receipt_refs": receipt_refs,
        "identity_validation_receipt_refs": _string_list(
            references.get("validation_receipt_refs")
        ),
        "lineage_refs": lineage_refs,
        "identity_lineage_links": _string_list(lineage.get("lineage_links")),
        "contribution_refs": contribution_refs,
        "identity_contribution_refs": _string_list(
            attribution.get("contribution_refs")
        ),
        "attribution_creator_node_id": attribution.get("creator_node_id"),
        "attribution_node_id": attribution.get("attribution_node_id"),
    }


def _load_runtime_json(path: Path, label: str) -> dict[str, Any]:
    return load_json_mapping(path, label, LocalRuntimeInspectError)


def _load_runtime_config(root: Path) -> LocalRuntimeConfig | None:
    config_path = root / LOCAL_RUNTIME_CONFIG_PATH
    if not config_path.exists():
        return None
    try:
        return load_local_runtime_config(config_path)
    except LocalRuntimeConfigError as exc:
        raise LocalRuntimeInspectError(str(exc)) from exc


def _configured_ref(config: LocalRuntimeConfig | None, path_key: str) -> str:
    if config is None:
        return DEFAULT_RUNTIME_PATHS[path_key]
    return config.paths[path_key]


def _configured_path(
    root: Path, config: LocalRuntimeConfig | None, path_key: str
) -> Path:
    return root / _configured_ref(config, path_key)


def _relative_ref(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _required_mapping(
    document: dict[str, Any], field_name: str, label: str
) -> dict[str, Any]:
    value = document.get(field_name)
    if not isinstance(value, dict):
        raise LocalRuntimeInspectError(
            f"{label} field {field_name!r} must be an object"
        )
    return value


def _required_text(document: dict[str, Any], field_name: str, label: str) -> str:
    value = document.get(field_name)
    if not isinstance(value, str) or value == "":
        raise LocalRuntimeInspectError(
            f"{label} field {field_name!r} must be a non-empty string"
        )
    return value


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise LocalRuntimeInspectError("runtime reference fields must be string lists")
    return list(value)


def _artifact_refs(root: Path, directory_ref: str) -> list[str]:
    path = root / directory_ref
    if not path.exists():
        return []
    return [
        f"{directory_ref}/{child.name}"
        for child in sorted(path.iterdir())
        if child.is_file() and child.suffix == ".json"
    ]


__all__ = [
    "LocalRestartError",
    "LocalRestartResult",
    "LocalRuntimeInspectError",
    "LocalShutdownError",
    "LocalShutdownResult",
    "LocalStartupError",
    "LocalStartupResult",
    "LocalValidationError",
    "inspect_local_node_runtime",
    "restart_local_node_runtime",
    "start_local_node_runtime",
    "stop_local_node_runtime",
    "validate_local_node_results",
]
