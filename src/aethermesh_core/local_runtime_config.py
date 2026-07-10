"""Validated local runtime configuration for Phase 1 node artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aethermesh_core.json_io import atomic_create_json, atomic_write_json

LOCAL_RUNTIME_CONFIG_VERSION = 1
LOCAL_RUNTIME_CONFIG_FILE = "local-runtime-config.json"


class LocalRuntimeConfigError(ValueError):
    """Raised when local runtime configuration cannot be trusted."""


@dataclass(frozen=True)
class LocalRuntimeConfig:
    """One explicit source of Phase 1 local runtime paths and creator identity."""

    root: Path
    creator_node_id: str
    identity_path: Path
    manifest_path: Path
    validation_receipts_dir: Path
    lineage_dir: Path
    contribution_attribution_dir: Path
    logs_dir: Path
    work_inputs_dir: Path
    work_outputs_dir: Path

    @property
    def config_path(self) -> Path:
        return self.root / LOCAL_RUNTIME_CONFIG_FILE

    @property
    def startup_log_path(self) -> Path:
        return self.logs_dir / "startup.log"

    def relative_ref(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise LocalRuntimeConfigError(
                "runtime config paths must stay inside the local runtime directory"
            ) from exc

    def runtime_directories(self) -> dict[str, str]:
        return {
            "manifests": self.relative_ref(self.manifest_path.parent),
            "receipts": self.relative_ref(self.validation_receipts_dir),
            "logs": self.relative_ref(self.logs_dir),
            "work_inputs": self.relative_ref(self.work_inputs_dir),
            "work_outputs": self.relative_ref(self.work_outputs_dir),
            "lineage": self.relative_ref(self.lineage_dir),
            "contribution_attribution": self.relative_ref(
                self.contribution_attribution_dir
            ),
        }


def load_or_create_local_runtime_config(
    runtime_dir: str | Path, *, creator_node_id: str
) -> LocalRuntimeConfig:
    """Load the config, or create the default local-only config on first run."""

    root = Path(runtime_dir)
    config_path = root / LOCAL_RUNTIME_CONFIG_FILE
    if config_path.exists():
        return load_local_runtime_config(
            runtime_dir, expected_creator_node_id=creator_node_id
        )
    document = default_local_runtime_config_document(creator_node_id=creator_node_id)
    try:
        root.mkdir(parents=True, exist_ok=True)
        atomic_create_json(config_path, document)
    except OSError as exc:
        raise LocalRuntimeConfigError(
            f"could not create local runtime config: {exc}"
        ) from exc
    return parse_local_runtime_config_document(root, document)


def load_local_runtime_config(
    runtime_dir: str | Path, *, expected_creator_node_id: str | None = None
) -> LocalRuntimeConfig:
    """Load and validate the Phase 1 local runtime config file."""

    root = Path(runtime_dir)
    path = root / LOCAL_RUNTIME_CONFIG_FILE
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except FileNotFoundError as exc:
        raise LocalRuntimeConfigError("local runtime config is missing") from exc
    except json.JSONDecodeError as exc:
        raise LocalRuntimeConfigError(
            f"local runtime config JSON is malformed: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise LocalRuntimeConfigError(
            f"could not read local runtime config: {exc}"
        ) from exc
    config = parse_local_runtime_config_document(root, document)
    if (
        expected_creator_node_id is not None
        and config.creator_node_id != expected_creator_node_id
    ):
        raise LocalRuntimeConfigError(
            "local runtime config creator_node_id does not match persisted identity"
        )
    return config


def default_local_runtime_config_document(*, creator_node_id: str) -> dict[str, object]:
    """Return the minimal Phase 1 local-only runtime config document."""

    _require_non_empty_text(creator_node_id, "creator_node_id")
    return {
        "version": LOCAL_RUNTIME_CONFIG_VERSION,
        "runtime_mode": "local_only",
        "creator_node_id": creator_node_id,
        "identity_path": "identity/creator-node.json",
        "manifest_path": "manifests/local-node-manifest.json",
        "validation_receipts_dir": "receipts",
        "lineage_dir": "lineage",
        "contribution_attribution_dir": "contributions",
        "logs_dir": "logs",
        "work_inputs_dir": "work/inputs",
        "work_outputs_dir": "work/outputs",
        "notes": {
            "creator_node_id": "Stable local creator node ID; do not regenerate during normal local runs. Use the explicit reset flow only when intentionally rotating identity."
        },
    }


def runtime_config_document(
    config: LocalRuntimeConfig, *, creator_node_id: str | None = None
) -> dict[str, object]:
    """Serialize config with local relative paths, preserving explicit path choices."""

    return {
        "version": LOCAL_RUNTIME_CONFIG_VERSION,
        "runtime_mode": "local_only",
        "creator_node_id": creator_node_id or config.creator_node_id,
        "identity_path": config.relative_ref(config.identity_path),
        "manifest_path": config.relative_ref(config.manifest_path),
        "validation_receipts_dir": config.relative_ref(config.validation_receipts_dir),
        "lineage_dir": config.relative_ref(config.lineage_dir),
        "contribution_attribution_dir": config.relative_ref(
            config.contribution_attribution_dir
        ),
        "logs_dir": config.relative_ref(config.logs_dir),
        "work_inputs_dir": config.relative_ref(config.work_inputs_dir),
        "work_outputs_dir": config.relative_ref(config.work_outputs_dir),
        "notes": {
            "creator_node_id": "Stable local creator node ID; do not regenerate during normal local runs. Use the explicit reset flow only when intentionally rotating identity."
        },
    }


def write_local_runtime_config(
    config: LocalRuntimeConfig, *, creator_node_id: str | None = None
) -> None:
    """Persist a validated local runtime config document."""

    document = runtime_config_document(config, creator_node_id=creator_node_id)
    parse_local_runtime_config_document(config.root, document)
    try:
        atomic_write_json(config.config_path, document)
    except OSError as exc:
        raise LocalRuntimeConfigError(
            f"could not write local runtime config: {exc}"
        ) from exc


def parse_local_runtime_config_document(
    root: Path, document: object
) -> LocalRuntimeConfig:
    """Parse a local runtime config mapping and resolve paths under ``root``."""

    if not isinstance(document, dict):
        raise LocalRuntimeConfigError("local runtime config must be a JSON object")
    if document.get("version") != LOCAL_RUNTIME_CONFIG_VERSION:
        raise LocalRuntimeConfigError("local runtime config must contain version 1")
    if document.get("runtime_mode") != "local_only":
        raise LocalRuntimeConfigError(
            "local runtime config runtime_mode must be local_only"
        )
    creator_node_id = _require_field_text(document, "creator_node_id")
    config = LocalRuntimeConfig(
        root=root,
        creator_node_id=creator_node_id,
        identity_path=_resolve_local_path(root, document, "identity_path"),
        manifest_path=_resolve_local_path(root, document, "manifest_path"),
        validation_receipts_dir=_resolve_local_path(
            root, document, "validation_receipts_dir"
        ),
        lineage_dir=_resolve_local_path(root, document, "lineage_dir"),
        contribution_attribution_dir=_resolve_local_path(
            root, document, "contribution_attribution_dir"
        ),
        logs_dir=_resolve_local_path(root, document, "logs_dir"),
        work_inputs_dir=_resolve_local_path(root, document, "work_inputs_dir"),
        work_outputs_dir=_resolve_local_path(root, document, "work_outputs_dir"),
    )
    for label, path in (
        ("identity_path", config.identity_path),
        ("manifest_path", config.manifest_path),
        ("validation_receipts_dir", config.validation_receipts_dir),
        ("lineage_dir", config.lineage_dir),
        ("contribution_attribution_dir", config.contribution_attribution_dir),
        ("logs_dir", config.logs_dir),
        ("work_inputs_dir", config.work_inputs_dir),
        ("work_outputs_dir", config.work_outputs_dir),
    ):
        config.relative_ref(path)
        if path == root:
            raise LocalRuntimeConfigError(
                f"local runtime config {label} must not point at runtime root"
            )
    return config


def _resolve_local_path(root: Path, document: dict[str, Any], field_name: str) -> Path:
    raw_path = _require_field_text(document, field_name)
    path = Path(raw_path)
    if path.is_absolute() or ".." in path.parts:
        raise LocalRuntimeConfigError(
            f"local runtime config {field_name} must be a local relative path"
        )
    return root / path


def _require_field_text(document: dict[str, Any], field_name: str) -> str:
    if field_name not in document:
        raise LocalRuntimeConfigError(
            f"local runtime config missing required field {field_name!r}"
        )
    return _require_non_empty_text(document[field_name], field_name)


def _require_non_empty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LocalRuntimeConfigError(
            f"local runtime config field {field_name!r} must be a non-empty string"
        )
    return value
