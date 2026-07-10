"""Local-first startup path for one developer AetherMesh node."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from aethermesh_core.identity import (
    IdentityPersistenceError,
    load_or_create_identity,
    reset_identity,
)
from aethermesh_core.json_io import atomic_create_json, atomic_write_json
from aethermesh_core.local_runtime_config import (
    LOCAL_RUNTIME_CONFIG_FILE,
    LocalRuntimeConfig,
    LocalRuntimeConfigError,
    load_local_runtime_config,
    load_or_create_local_runtime_config,
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
    "manifests": "manifests",
    "receipts": "receipts",
    "logs": "logs",
    "work_inputs": "work/inputs",
    "work_outputs": "work/outputs",
    "lineage": "lineage",
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
    config_path = root / LOCAL_RUNTIME_CONFIG_FILE
    try:
        bootstrap_config = (
            load_local_runtime_config(root) if config_path.exists() else None
        )
    except LocalRuntimeConfigError as exc:
        raise LocalStartupError(str(exc)) from exc
    identity_path = (
        bootstrap_config.identity_path
        if bootstrap_config is not None
        else root / "identity" / "creator-node.json"
    )
    manifest_path = (
        bootstrap_config.manifest_path
        if bootstrap_config is not None
        else root / REQUIRED_RUNTIME_DIRS["manifests"] / "local-node-manifest.json"
    )
    identity_existed = identity_path.exists()
    if identity_existed and not reset_creator_identity and not manifest_path.exists():
        raise LocalStartupError(
            "required startup manifest is missing; refusing to recreate manifest for an existing identity"
        )
    if bootstrap_config is None:
        _ensure_runtime_dirs(root)
    else:
        _ensure_runtime_dirs(root, bootstrap_config)
    if reset_creator_identity and identity_existed:
        try:
            reset_identity(
                identity_path,
                reason="explicit local node startup reset",
                quarantine_dir=root / "identity" / "identity-quarantine",
                audit_receipt_path=root / "receipts" / "identity-reset-receipts.json",
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
    if reset_creator_identity and identity_existed and bootstrap_config is not None:
        try:
            write_local_runtime_config(
                bootstrap_config, creator_node_id=creator_node_id
            )
        except LocalRuntimeConfigError as exc:
            raise LocalStartupError(str(exc)) from exc
    try:
        config = load_or_create_local_runtime_config(
            root, creator_node_id=creator_node_id
        )
    except LocalRuntimeConfigError as exc:
        raise LocalStartupError(str(exc)) from exc
    manifest_path = config.manifest_path
    if reset_creator_identity and identity_existed:
        _write_default_manifest(
            manifest_path,
            node_id=identity.node_id,
            creator_node_id=creator_node_id,
            runtime_metadata=capture_version_metadata(),
        )
    elif not manifest_path.exists():
        _create_default_manifest(
            manifest_path,
            node_id=identity.node_id,
            creator_node_id=creator_node_id,
            runtime_metadata=capture_version_metadata(),
        )
    manifest = _load_manifest(manifest_path)
    _validate_manifest(
        manifest,
        expected_node_id=identity.node_id,
        expected_creator_node_id=creator_node_id,
    )
    _ensure_manifest_directories(config, manifest)
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    manifest_hash = _document_hash(manifest)
    receipt_ref = _next_artifact_ref(
        config, config.validation_receipts_dir, "startup-validation", timestamp
    )
    lineage_ref = _next_artifact_ref(
        config, config.lineage_dir, "startup-lineage", timestamp
    )
    receipt_path = root / receipt_ref
    lineage_path = root / lineage_ref
    log_path = config.startup_log_path
    receipt = _startup_receipt(
        node_id=identity.node_id,
        creator_node_id=creator_node_id,
        manifest_ref=config.relative_ref(manifest_path),
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
        manifest_ref=config.relative_ref(manifest_path),
        manifest_hash=manifest_hash,
        receipt_ref=receipt_ref,
        runtime_metadata=validate_version_metadata(manifest["runtime_version"]),
        timestamp=timestamp,
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
        identity_path=config.relative_ref(identity_path),
        manifest_path=config.relative_ref(manifest_path),
        manifest_hash=manifest_hash,
        validation_receipt_path=receipt_ref,
        lineage_path=lineage_ref,
        log_path=config.relative_ref(log_path),
        runtime_directories=config.runtime_directories(),
        validation_result="passed",
    )


def _ensure_runtime_dirs(root: Path, config: LocalRuntimeConfig | None = None) -> None:
    paths = (
        config.runtime_directories().values()
        if config is not None
        else REQUIRED_RUNTIME_DIRS.values()
    )
    for relative_path in paths:
        path = root / relative_path
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise LocalStartupError(
                f"required runtime directory {relative_path!r} is invalid: {exc}"
            ) from exc


def _ensure_manifest_directories(
    config: LocalRuntimeConfig, manifest: dict[str, object]
) -> None:
    directories = manifest["work_directories"]
    if not isinstance(directories, dict):
        raise LocalStartupError("startup manifest work_directories must be an object")
    for key, expected in config.runtime_directories().items():
        value = directories.get(key)
        if value != expected:
            raise LocalStartupError(
                f"startup manifest work_directories.{key} must be {expected!r}"
            )
        path = config.root / expected
        if not path.is_dir():
            raise LocalStartupError(
                f"required runtime directory {expected!r} is not a directory"
            )


def _create_default_manifest(
    path: Path,
    *,
    node_id: str,
    creator_node_id: str,
    runtime_metadata: dict[str, object],
) -> None:
    document = _default_manifest_document(
        node_id=node_id,
        creator_node_id=creator_node_id,
        runtime_metadata=runtime_metadata,
    )
    try:
        atomic_create_json(path, document)
    except OSError as exc:
        raise LocalStartupError(f"could not create startup manifest: {exc}") from exc


def _write_default_manifest(
    path: Path,
    *,
    node_id: str,
    creator_node_id: str,
    runtime_metadata: dict[str, object],
) -> None:
    document = _default_manifest_document(
        node_id=node_id,
        creator_node_id=creator_node_id,
        runtime_metadata=runtime_metadata,
    )
    try:
        atomic_write_json(path, document)
    except OSError as exc:
        raise LocalStartupError(f"could not write startup manifest: {exc}") from exc


def _default_manifest_document(
    *, node_id: str, creator_node_id: str, runtime_metadata: dict[str, object]
) -> dict[str, object]:
    return {
        "version": LOCAL_STARTUP_MANIFEST_VERSION,
        "manifest_type": "local_node_startup",
        "node": {"node_id": node_id, "creator_node_id": creator_node_id},
        "runtime_version": runtime_metadata,
        "capabilities": list(DEFAULT_LOCAL_CAPABILITIES),
        "work_directories": dict(REQUIRED_RUNTIME_DIRS),
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
    if manifest.get("version") != LOCAL_STARTUP_MANIFEST_VERSION:
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
    config: LocalRuntimeConfig, directory: Path, stem: str, timestamp: str
) -> str:
    slug = timestamp.replace(":", "").replace("+", "Z")
    index = len(tuple(directory.glob(f"{stem}-*.json"))) + 1
    return f"{config.relative_ref(directory)}/{stem}-{slug}-{index:04d}.json"


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
            "configuration": LOCAL_RUNTIME_CONFIG_FILE,
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
