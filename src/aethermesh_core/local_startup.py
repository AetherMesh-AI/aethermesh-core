"""Local-first startup path for one developer AetherMesh node."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import cast

from aethermesh_core.identity import (
    IdentityPersistenceError,
    load_or_create_identity,
    reset_identity,
)
from aethermesh_core.json_io import atomic_create_json, atomic_write_json
from aethermesh_core.local_runtime_config import (
    DEFAULT_RUNTIME_PATHS,
    LOCAL_RUNTIME_CONFIG_PATH,
    LocalRuntimeConfig,
    LocalRuntimeConfigError,
    load_local_runtime_config,
    load_or_create_local_runtime_config,
    validate_runtime_path_boundaries,
    write_local_runtime_config,
)
from aethermesh_core.version_metadata import (
    VersionMetadataError,
    capture_version_metadata,
    validate_version_metadata,
)

LOCAL_STARTUP_MANIFEST_VERSION = 1
LOCAL_STARTUP_RECEIPT_VERSION = 1
LOCAL_STARTUP_LINEAGE_VERSION = 1
DEFAULT_LOCAL_CAPABILITIES = ("local.echo", "local.validation", "local.receipts")
REQUIRED_RUNTIME_DIRS = {
    "manifests": "manifest",
    "receipts": "validation_receipts",
    "logs": "log",
    "work_inputs": "work_inputs",
    "work_outputs": "work_outputs",
    "lineage": "lineage",
    "contribution_attribution": "contribution_attribution",
}


class LocalStartupError(ValueError):
    """Raised when local node startup cannot fail closed safely."""


@dataclass(frozen=True)
class LocalStartupResult:
    """Serializable summary for one accepted local node startup."""

    node_id: str
    creator_node_id: str
    identity_path: str
    manifest_path: str
    manifest_hash: str
    validation_receipt_path: str
    lineage_path: str
    log_path: str
    runtime_directories: dict[str, str]
    validation_result: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable startup summary with local-only refs."""

        return {
            "node_id": self.node_id,
            "creator_node_id": self.creator_node_id,
            "identity_path": self.identity_path,
            "manifest_path": self.manifest_path,
            "manifest_hash": self.manifest_hash,
            "validation_receipt_path": self.validation_receipt_path,
            "lineage_path": self.lineage_path,
            "log_path": self.log_path,
            "runtime_directories": dict(self.runtime_directories),
            "validation_result": self.validation_result,
            "network_mode": "local-only-no-p2p",
        }


def start_local_node(
    runtime_dir: str | Path, *, reset_creator_identity: bool = False
) -> LocalStartupResult:
    """Initialize one local node runtime without external services."""

    root = Path(runtime_dir)
    config_path = root / LOCAL_RUNTIME_CONFIG_PATH
    resolved_root = root.resolve()
    if not config_path.resolve().is_relative_to(resolved_root):
        raise LocalStartupError(
            "local runtime config must stay within the runtime directory"
        )
    preloaded_config = _load_existing_config(config_path)
    try:
        validate_runtime_path_boundaries(root, preloaded_config)
    except LocalRuntimeConfigError as exc:
        raise LocalStartupError(str(exc)) from exc
    if preloaded_config is None and any(
        (root / relative_ref).exists() or (root / relative_ref).is_symlink()
        for relative_ref in DEFAULT_RUNTIME_PATHS.values()
    ):
        raise LocalStartupError(
            "required local runtime config is missing; refusing to reuse existing runtime artifacts"
        )
    identity_path = _configured_path(root, preloaded_config, "identity")
    manifest_path = _configured_path(root, preloaded_config, "manifest")
    identity_existed = identity_path.exists()
    if preloaded_config is not None and not identity_existed:
        raise LocalStartupError(
            "required creator node identity is missing; refusing to regenerate preserved identity"
        )
    if identity_existed and not reset_creator_identity and not manifest_path.exists():
        raise LocalStartupError(
            "required startup manifest is missing; refusing to recreate manifest for an existing identity"
        )
    _ensure_runtime_dirs(root, preloaded_config)
    if reset_creator_identity and identity_existed:
        try:
            reset_identity(
                identity_path,
                reason="explicit local node startup reset",
                quarantine_dir=identity_path.parent / "identity-quarantine",
                audit_receipt_path=(
                    _configured_path(root, preloaded_config, "validation_receipts")
                    / "identity-reset-receipts.json"
                ),
                rotate_creator_identity=True,
            )
        except IdentityPersistenceError as exc:
            raise LocalStartupError(str(exc)) from exc
    try:
        identity = load_or_create_identity(identity_path)
    except IdentityPersistenceError as exc:
        raise LocalStartupError(str(exc)) from exc
    identity_document = _load_json_object(identity_path, "identity")
    creator_node_id = _identity_creator_node_id(identity_document)
    try:
        if reset_creator_identity and identity_existed:
            existing_config = cast(LocalRuntimeConfig, preloaded_config)
            config = LocalRuntimeConfig(
                node_id=identity.node_id,
                creator_node_id=creator_node_id,
                paths=dict(existing_config.paths),
            )
            write_local_runtime_config(config_path, config)
        else:
            config = load_or_create_local_runtime_config(
                config_path,
                node_id=identity.node_id,
                creator_node_id=creator_node_id,
            )
    except LocalRuntimeConfigError as exc:
        raise LocalStartupError(str(exc)) from exc
    identity_path = config.resolve_path(root, "identity")
    manifest_path = config.resolve_path(root, "manifest")
    runtime_dirs = _runtime_dirs(config)
    _ensure_runtime_dirs(root, config)
    if reset_creator_identity and identity_existed:
        _write_default_manifest(
            manifest_path,
            node_id=identity.node_id,
            creator_node_id=creator_node_id,
            runtime_metadata=capture_version_metadata(),
            runtime_dirs=runtime_dirs,
            replace_existing=True,
        )
    elif not manifest_path.exists():
        _write_default_manifest(
            manifest_path,
            node_id=identity.node_id,
            creator_node_id=creator_node_id,
            runtime_metadata=capture_version_metadata(),
            runtime_dirs=runtime_dirs,
            replace_existing=False,
        )
    manifest = _load_manifest(manifest_path)
    _validate_manifest(
        manifest,
        expected_node_id=identity.node_id,
        expected_creator_node_id=creator_node_id,
    )
    _ensure_manifest_directories(root, manifest, runtime_dirs=runtime_dirs)
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    manifest_hash = _document_hash(manifest)
    receipt_ref = _next_artifact_ref(
        root, config, "validation_receipts", "startup-validation", timestamp
    )
    lineage_ref = _next_artifact_ref(
        root, config, "lineage", "startup-lineage", timestamp
    )
    receipt_path = root / receipt_ref
    lineage_path = root / lineage_ref
    log_path = config.resolve_path(root, "log")
    receipt = _startup_receipt(
        node_id=identity.node_id,
        creator_node_id=creator_node_id,
        manifest_ref=_relative_ref(root, manifest_path),
        manifest_hash=manifest_hash,
        runtime_metadata=validate_version_metadata(manifest["runtime_version"]),
        timestamp=timestamp,
    )
    try:
        atomic_create_json(receipt_path, receipt)
    except OSError as exc:
        raise LocalStartupError(
            f"could not create startup validation receipt: {exc}"
        ) from exc
    lineage = _startup_lineage(
        node_id=identity.node_id,
        creator_node_id=creator_node_id,
        manifest_ref=_relative_ref(root, manifest_path),
        manifest_hash=manifest_hash,
        receipt_ref=receipt_ref,
        runtime_metadata=validate_version_metadata(manifest["runtime_version"]),
        timestamp=timestamp,
        config_ref=LOCAL_RUNTIME_CONFIG_PATH,
    )
    try:
        atomic_create_json(lineage_path, lineage)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "event": "local_node_startup",
                        "timestamp": timestamp,
                        "node_id": identity.node_id,
                        "creator_node_id": creator_node_id,
                        "manifest_hash": manifest_hash,
                        "validation_result": "passed",
                    },
                    sort_keys=True,
                )
            )
            handle.write("\n")
    except OSError as exc:
        raise LocalStartupError(
            f"could not record startup lineage or log: {exc}"
        ) from exc
    return LocalStartupResult(
        node_id=identity.node_id,
        creator_node_id=creator_node_id,
        identity_path=_relative_ref(root, identity_path),
        manifest_path=_relative_ref(root, manifest_path),
        manifest_hash=manifest_hash,
        validation_receipt_path=receipt_ref,
        lineage_path=lineage_ref,
        log_path=_relative_ref(root, log_path),
        runtime_directories=runtime_dirs,
        validation_result="passed",
    )


def _load_existing_config(path: Path) -> LocalRuntimeConfig | None:
    if not path.exists():
        return None
    try:
        return load_local_runtime_config(path)
    except LocalRuntimeConfigError as exc:
        raise LocalStartupError(str(exc)) from exc


def _configured_path(
    root: Path, config: LocalRuntimeConfig | None, path_key: str
) -> Path:
    if config is not None:
        return config.resolve_path(root, path_key)
    return root / DEFAULT_RUNTIME_PATHS[path_key]


def _runtime_dirs(config: LocalRuntimeConfig) -> dict[str, str]:
    runtime_dirs: dict[str, str] = {}
    for key, path_key in REQUIRED_RUNTIME_DIRS.items():
        configured_ref = config.paths[path_key]
        if key in {"manifests", "logs"}:
            runtime_dirs[key] = Path(configured_ref).parent.as_posix()
        else:
            runtime_dirs[key] = configured_ref
    return runtime_dirs


def _ensure_runtime_dirs(root: Path, config: LocalRuntimeConfig | None) -> None:
    runtime_dirs = (
        _runtime_dirs(config)
        if config is not None
        else {
            key: (
                Path(DEFAULT_RUNTIME_PATHS[path_key]).parent.as_posix()
                if key in {"manifests", "logs"}
                else DEFAULT_RUNTIME_PATHS[path_key]
            )
            for key, path_key in REQUIRED_RUNTIME_DIRS.items()
        }
    )
    for relative_path in runtime_dirs.values():
        path = root / relative_path
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise LocalStartupError(
                f"required runtime directory {relative_path!r} is invalid: {exc}"
            ) from exc


def _ensure_manifest_directories(
    root: Path, manifest: dict[str, object], *, runtime_dirs: dict[str, str]
) -> None:
    directories = manifest["work_directories"]
    if not isinstance(directories, dict):
        raise LocalStartupError("startup manifest work_directories must be an object")
    for key, expected in runtime_dirs.items():
        value = directories.get(key)
        if value != expected:
            raise LocalStartupError(
                f"startup manifest work_directories.{key} must be {expected!r}"
            )
        path = root / expected
        if not path.is_dir():
            raise LocalStartupError(
                f"required runtime directory {expected!r} is not a directory"
            )


def _write_default_manifest(
    path: Path,
    *,
    node_id: str,
    creator_node_id: str,
    runtime_metadata: dict[str, object],
    runtime_dirs: dict[str, str],
    replace_existing: bool,
) -> None:
    document = _default_manifest_document(
        node_id=node_id,
        creator_node_id=creator_node_id,
        runtime_metadata=runtime_metadata,
        runtime_dirs=runtime_dirs,
    )
    action = "write" if replace_existing else "create"
    try:
        if replace_existing:
            atomic_write_json(path, document)
        else:
            atomic_create_json(path, document)
    except OSError as exc:
        raise LocalStartupError(f"could not {action} startup manifest: {exc}") from exc


def _default_manifest_document(
    *,
    node_id: str,
    creator_node_id: str,
    runtime_metadata: dict[str, object],
    runtime_dirs: dict[str, str],
) -> dict[str, object]:
    return {
        "version": LOCAL_STARTUP_MANIFEST_VERSION,
        "manifest_type": "local_node_startup",
        "node": {"node_id": node_id, "creator_node_id": creator_node_id},
        "runtime_version": runtime_metadata,
        "capabilities": list(DEFAULT_LOCAL_CAPABILITIES),
        "work_directories": dict(runtime_dirs),
        "validation": {
            "startup_validation_required": True,
            "fail_closed": True,
            "external_services_required": False,
            "accepts_work_after_startup_validation": True,
        },
    }


def _load_manifest(path: Path) -> dict[str, object]:
    return _load_json_object(path, "startup manifest")


def _load_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        raise LocalStartupError(f"{label} JSON is malformed: {exc.msg}") from exc
    except OSError as exc:
        raise LocalStartupError(f"could not read {label}: {exc}") from exc
    if not isinstance(document, dict):
        raise LocalStartupError(f"{label} must be a JSON object")
    return document


def _validate_manifest(
    manifest: dict[str, object], *, expected_node_id: str, expected_creator_node_id: str
) -> None:
    if (
        type(manifest.get("version")) is not int
        or manifest["version"] != LOCAL_STARTUP_MANIFEST_VERSION
    ):
        raise LocalStartupError("startup manifest must contain version 1")
    if manifest.get("manifest_type") != "local_node_startup":
        raise LocalStartupError("startup manifest_type must be local_node_startup")
    node = manifest.get("node")
    if not isinstance(node, dict):
        raise LocalStartupError("startup manifest node must be an object")
    if node.get("node_id") != expected_node_id:
        raise LocalStartupError("startup manifest node_id does not match identity")
    if node.get("creator_node_id") != expected_creator_node_id:
        raise LocalStartupError(
            "startup manifest creator_node_id does not match identity"
        )
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise LocalStartupError(
            "startup manifest capabilities must be a non-empty list"
        )
    if any(
        not isinstance(capability, str) or not capability for capability in capabilities
    ):
        raise LocalStartupError(
            "startup manifest capabilities must be non-empty strings"
        )
    try:
        validate_version_metadata(manifest.get("runtime_version"))
    except VersionMetadataError as exc:
        raise LocalStartupError(f"startup manifest {exc}") from exc
    validation = manifest.get("validation")
    if not isinstance(validation, dict):
        raise LocalStartupError("startup manifest validation must be an object")
    required_flags = {
        "startup_validation_required": True,
        "fail_closed": True,
        "external_services_required": False,
        "accepts_work_after_startup_validation": True,
    }
    for key, expected in required_flags.items():
        if validation.get(key) is not expected:
            raise LocalStartupError(
                f"startup manifest validation.{key} must be {expected}"
            )


def _identity_creator_node_id(document: dict[str, object]) -> str:
    node = document.get("node")
    if not isinstance(node, dict):
        raise LocalStartupError("identity node must be an object")
    creator_node_id = node.get("creator_node_id")
    if not isinstance(creator_node_id, str) or not creator_node_id:
        raise LocalStartupError("identity creator_node_id must be a non-empty string")
    return creator_node_id


def _document_hash(document: dict[str, object]) -> str:
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return "sha256:" + sha256(encoded).hexdigest()


def _next_artifact_ref(
    root: Path,
    config: LocalRuntimeConfig,
    directory_key: str,
    stem: str,
    timestamp: str,
) -> str:
    directory = config.paths[directory_key]
    slug = timestamp.replace(":", "").replace("+", "Z")
    index = len(tuple((root / directory).glob(f"{stem}-*.json"))) + 1
    return f"{directory}/{stem}-{slug}-{index:04d}.json"


def _relative_ref(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _startup_receipt(
    *,
    node_id: str,
    creator_node_id: str,
    manifest_ref: str,
    manifest_hash: str,
    runtime_metadata: dict[str, object],
    timestamp: str,
) -> dict[str, object]:
    return {
        "version": LOCAL_STARTUP_RECEIPT_VERSION,
        "receipt_type": "startup_validation",
        "timestamp": timestamp,
        "node_id": node_id,
        "creator_node_id": creator_node_id,
        "manifest_ref": manifest_ref,
        "manifest_hash": manifest_hash,
        "runtime_version": runtime_metadata,
        "validation_result": {
            "accepted": True,
            "status": "passed",
            "fail_closed": True,
        },
        "contribution_attribution": {
            "creator_node_id": creator_node_id,
            "attribution_node_id": node_id,
            "event": "local_node_startup",
            "scoring_applied": False,
        },
        "network_mode": "local-only-no-p2p",
    }


def _startup_lineage(
    *,
    node_id: str,
    creator_node_id: str,
    manifest_ref: str,
    manifest_hash: str,
    receipt_ref: str,
    runtime_metadata: dict[str, object],
    timestamp: str,
    config_ref: str,
) -> dict[str, object]:
    return {
        "version": LOCAL_STARTUP_LINEAGE_VERSION,
        "lineage_type": "local_node_startup",
        "timestamp": timestamp,
        "node_id": node_id,
        "creator_node_id": creator_node_id,
        "inputs": {
            "manifest_ref": manifest_ref,
            "manifest_hash": manifest_hash,
            "runtime_version": runtime_metadata,
            "configuration": config_ref,
        },
        "outputs": {"validation_receipt_ref": receipt_ref},
        "contribution_attribution": {
            "creator_node_id": creator_node_id,
            "attribution_node_id": node_id,
            "event": "local_node_startup",
            "scoring_applied": False,
        },
        "network_mode": "local-only-no-p2p",
    }
