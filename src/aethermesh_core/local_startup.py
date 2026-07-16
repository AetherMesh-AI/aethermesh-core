"""Local-first startup path for one developer AetherMesh node."""

from __future__ import annotations

import json
import re
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
from aethermesh_core.local_audit_event import append_local_audit_event
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

    def __init__(self, detail: str) -> None:
        detail = _redact_local_paths(detail)
        self.code, self.phase, self.guidance = _classify_startup_error(detail)
        self.detail = detail
        super().__init__(detail)

    def __str__(self) -> str:
        return (
            f"[{self.code}] startup phase {self.phase} failed: {self.detail}. "
            f"Local fix: {self.guidance}"
        )


def _redact_local_paths(detail: str) -> str:
    """Keep startup errors shareable by removing absolute host paths."""

    detail = re.sub(
        r"(?P<quote>['\"])(?:[A-Za-z]:[\\/]|/|~/).*?(?P=quote)",
        r"\g<quote><local-path>\g<quote>",
        detail,
    )
    detail = re.sub(r"(?<![\w.])(?:[A-Za-z]:[\\/]|/)[^\s'\"]+", "<local-path>", detail)
    return re.sub(r"(?<![\w.])~/[^\s'\"]+", "<local-path>", detail)


def _classify_startup_error(detail: str) -> tuple[str, str, str]:
    """Attach stable automation fields without including local configuration values."""

    lowered = detail.lower()
    if "local runtime config" in lowered:
        return (
            "STARTUP_CONFIG_INVALID",
            "config_load",
            "correct the named field in runtime-config.json using the expected format",
        )
    if "manifest" in lowered:
        return (
            "STARTUP_MANIFEST_INVALID",
            "manifest_validation",
            "restore a valid local startup manifest matching the preserved identity",
        )
    if (
        "creator_node_id" in lowered
        or "creator node identity" in lowered
        or "identity" in lowered
    ):
        return (
            "STARTUP_IDENTITY_INVALID",
            "identity_load",
            "restore the preserved local identity and its non-empty node.creator_node_id",
        )
    if "validation receipt" in lowered or "receipts" in lowered:
        return (
            "STARTUP_RECEIPT_STORAGE_UNAVAILABLE",
            "storage_check",
            "make config field paths.validation_receipts a writable local directory",
        )
    if "lineage" in lowered:
        return (
            "STARTUP_LINEAGE_STORAGE_UNAVAILABLE",
            "storage_check",
            "make config field paths.lineage a writable local directory",
        )
    if "contribution" in lowered or "attribution" in lowered:
        return (
            "STARTUP_ATTRIBUTION_STORAGE_UNAVAILABLE",
            "storage_check",
            "make config field paths.contribution_attribution a writable local directory",
        )
    return (
        "STARTUP_STORAGE_UNAVAILABLE",
        "storage_check",
        "correct the named local runtime path and ensure it is writable",
    )


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
    if root.exists() and not root.is_dir():
        raise LocalStartupError("local runtime path must be a directory")
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
    if preloaded_config is None and root.exists() and _contains_runtime_artifacts(root):
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
    if preloaded_config is not None:
        try:
            preserved_identity = load_or_create_identity(identity_path)
        except IdentityPersistenceError as exc:
            raise LocalStartupError(str(exc)) from exc
        preserved_identity_document = _load_json_object(identity_path, "identity")
        preserved_creator_node_id = _identity_creator_node_id(
            preserved_identity_document
        )
        if preloaded_config.node_id != preserved_identity.node_id:
            raise LocalStartupError(
                "local runtime config node.node_id does not match identity"
            )
        if preloaded_config.creator_node_id != preserved_creator_node_id:
            raise LocalStartupError(
                "local runtime config node.creator_node_id does not match identity"
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
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat()
    receipt_ref = _next_artifact_ref(
        root, config, "validation_receipts", "startup-validation", timestamp
    )
    advertisement_action = "refreshed"
    if reset_creator_identity and identity_existed:
        advertisement_action = "replaced"
        _write_default_manifest(
            manifest_path,
            node_id=identity.node_id,
            creator_node_id=creator_node_id,
            runtime_metadata=capture_version_metadata(),
            runtime_dirs=runtime_dirs,
            manifest_ref=_relative_ref(root, manifest_path),
            validation_receipt_ref=receipt_ref,
            replace_existing=True,
        )
    elif not manifest_path.exists():
        advertisement_action = "created"
        _write_default_manifest(
            manifest_path,
            node_id=identity.node_id,
            creator_node_id=creator_node_id,
            runtime_metadata=capture_version_metadata(),
            runtime_dirs=runtime_dirs,
            manifest_ref=_relative_ref(root, manifest_path),
            validation_receipt_ref=receipt_ref,
            replace_existing=False,
        )
    manifest = _load_manifest(manifest_path)
    if "capability_advertisements" not in manifest:
        advertisement_action = "created"
        manifest["capability_advertisements"] = _default_capability_advertisements(
            creator_node_id=creator_node_id,
            manifest_ref=_relative_ref(root, manifest_path),
            validation_receipt_ref=receipt_ref,
        )
        try:
            atomic_write_json(manifest_path, manifest)
        except OSError as exc:
            raise LocalStartupError(
                f"could not upgrade startup manifest capability advertisement: {exc}"
            ) from exc
    _validate_manifest(
        manifest,
        expected_node_id=identity.node_id,
        expected_creator_node_id=creator_node_id,
    )
    _ensure_manifest_directories(root, manifest, runtime_dirs=runtime_dirs)
    manifest_hash = _document_hash(manifest)
    runtime_metadata = validate_version_metadata(manifest["runtime_version"])
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
        runtime_metadata=runtime_metadata,
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
        runtime_metadata=runtime_metadata,
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
                        "event_type": "node_startup",
                        "timestamp": timestamp,
                        "node_id": identity.node_id,
                        "creator_node_id": creator_node_id,
                        "manifest_ref": _relative_ref(root, manifest_path),
                        "manifest_hash": manifest_hash,
                        "lineage_ref": lineage_ref,
                        "local_run_id": f"local-startup:{receipt_ref}",
                        "software_version": runtime_metadata,
                        "validation_status": "passed",
                        "contribution_attribution": {
                            "creator_node_id": creator_node_id,
                            "attribution_node_id": identity.node_id,
                            "event": "local_node_startup",
                            "scoring_applied": False,
                        },
                    },
                    sort_keys=True,
                )
            )
            handle.write("\n")
        _append_capability_advertisement_audit_events(
            root,
            advertisements=manifest["capability_advertisements"],
            action=advertisement_action,
            timestamp=timestamp.replace("+00:00", "Z"),
            node_id=identity.node_id,
            creator_node_id=creator_node_id,
            manifest_ref=_relative_ref(root, manifest_path),
            manifest_hash=manifest_hash,
            validation_receipt_ref=receipt_ref,
            lineage_ref=lineage_ref,
        )
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
    if path.is_symlink() and not path.exists():
        raise LocalStartupError(
            "local runtime config path is a dangling filesystem link"
        )
    if not path.exists():
        return None
    try:
        return load_local_runtime_config(path)
    except LocalRuntimeConfigError as exc:
        raise LocalStartupError(str(exc)) from exc


def _contains_runtime_artifacts(root: Path) -> bool:
    """Return whether a config-less root contains more than empty directories."""

    return any(path.is_symlink() or not path.is_dir() for path in root.rglob("*"))


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
        {
            path_key: relative_path
            for path_key, relative_path in config.paths.items()
            if path_key in REQUIRED_RUNTIME_DIRS.values()
        }
        if config is not None
        else {
            path_key: (
                Path(DEFAULT_RUNTIME_PATHS[path_key]).parent.as_posix()
                if key in {"manifests", "logs"}
                else DEFAULT_RUNTIME_PATHS[path_key]
            )
            for key, path_key in REQUIRED_RUNTIME_DIRS.items()
        }
    )
    for path_key, relative_path in runtime_dirs.items():
        if path_key in {"manifest", "log"}:
            relative_path = Path(relative_path).parent.as_posix()
        path = root / relative_path
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise LocalStartupError(
                f"config field paths.{path_key} requires a writable local directory: {exc}"
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
    manifest_ref: str,
    validation_receipt_ref: str,
    replace_existing: bool,
) -> None:
    document = _default_manifest_document(
        node_id=node_id,
        creator_node_id=creator_node_id,
        runtime_metadata=runtime_metadata,
        runtime_dirs=runtime_dirs,
        manifest_ref=manifest_ref,
        validation_receipt_ref=validation_receipt_ref,
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
    manifest_ref: str,
    validation_receipt_ref: str,
) -> dict[str, object]:
    return {
        "version": LOCAL_STARTUP_MANIFEST_VERSION,
        "manifest_type": "local_node_startup",
        "node": {"node_id": node_id, "creator_node_id": creator_node_id},
        "runtime_version": runtime_metadata,
        "capabilities": list(DEFAULT_LOCAL_CAPABILITIES),
        "capability_advertisements": _default_capability_advertisements(
            creator_node_id=creator_node_id,
            manifest_ref=manifest_ref,
            validation_receipt_ref=validation_receipt_ref,
        ),
        "work_directories": dict(runtime_dirs),
        "validation": {
            "startup_validation_required": True,
            "fail_closed": True,
            "external_services_required": False,
            "accepts_work_after_startup_validation": True,
        },
    }


def _default_capability_advertisements(
    *, creator_node_id: str, manifest_ref: str, validation_receipt_ref: str
) -> list[dict[str, object]]:
    return [
        {
            "capability_id": "local.manifest-validation",
            "name": "Local startup manifest validation",
            "version": "1.0.0",
            "description": "Validates one local startup manifest before accepting local work.",
            "supported_input": {
                "format": "application/json",
                "shape": "local_node_startup manifest",
            },
            "supported_output": {
                "format": "application/json",
                "shape": "startup_validation receipt",
            },
            "creator_node_id": creator_node_id,
            "validation": {
                "check_name": "startup-manifest-validation",
                "required_receipt_ref": validation_receipt_ref,
            },
            "lineage": {"source_manifest_ref": manifest_ref},
            "contribution_attribution": {
                "creator_node_id": creator_node_id,
                "work_record_ref": validation_receipt_ref,
            },
            "network_mode": "local-only-no-p2p",
        }
    ]


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
    advertisements = manifest.get("capability_advertisements")
    _validate_capability_advertisements(
        advertisements,
        expected_creator_node_id=expected_creator_node_id,
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


def _validate_capability_advertisements(
    advertisements: object, *, expected_creator_node_id: str
) -> None:
    if not isinstance(advertisements, list) or not advertisements:
        raise LocalStartupError(
            "startup manifest capability_advertisements must be a non-empty list"
        )
    required_strings = ("capability_id", "name", "version", "description")
    for index, advertisement in enumerate(advertisements):
        context = f"startup manifest capability_advertisements[{index}]"
        if not isinstance(advertisement, dict):
            raise LocalStartupError(f"{context} must be an object")
        for field in required_strings:
            if (
                not isinstance(advertisement.get(field), str)
                or not advertisement[field]
            ):
                raise LocalStartupError(f"{context}.{field} must be a non-empty string")
        for field in ("supported_input", "supported_output", "validation", "lineage"):
            if not isinstance(advertisement.get(field), dict):
                raise LocalStartupError(f"{context}.{field} must be an object")
        for field in ("supported_input", "supported_output"):
            shape = advertisement[field]
            if not isinstance(shape.get("format"), str) or not isinstance(
                shape.get("shape"), str
            ):
                raise LocalStartupError(
                    f"{context}.{field} must describe format and shape"
                )
        validation = advertisement["validation"]
        if not isinstance(validation.get("check_name"), str) or not isinstance(
            validation.get("required_receipt_ref"), str
        ):
            raise LocalStartupError(
                f"{context}.validation must reference a local receipt"
            )
        lineage = advertisement["lineage"]
        if not isinstance(lineage.get("source_manifest_ref"), str):
            raise LocalStartupError(f"{context}.lineage must reference its manifest")
        attribution = advertisement.get("contribution_attribution")
        if (
            not isinstance(attribution, dict)
            or attribution.get("creator_node_id") != expected_creator_node_id
            or not isinstance(attribution.get("work_record_ref"), str)
        ):
            raise LocalStartupError(f"{context}.contribution_attribution is invalid")
        if advertisement.get("creator_node_id") != expected_creator_node_id:
            raise LocalStartupError(
                f"{context}.creator_node_id does not match identity"
            )
        if advertisement.get("network_mode") != "local-only-no-p2p":
            raise LocalStartupError(f"{context}.network_mode must be local-only-no-p2p")


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


def _append_capability_advertisement_audit_events(
    root: Path,
    *,
    advertisements: object,
    action: str,
    timestamp: str,
    node_id: str,
    creator_node_id: str,
    manifest_ref: str,
    manifest_hash: str,
    validation_receipt_ref: str,
    lineage_ref: str,
) -> None:
    """Append one digest-only audit event for each validated local claim."""

    for event_sequence, advertisement in enumerate(
        cast(list[dict[str, object]], advertisements), start=1
    ):
        validation = cast(dict[str, object], advertisement["validation"])
        attribution = cast(dict[str, object], advertisement["contribution_attribution"])
        required_receipt_ref = cast(str, validation["required_receipt_ref"])
        work_record_ref = cast(str, attribution["work_record_ref"])
        capability_id = cast(str, advertisement["capability_id"])
        append_local_audit_event(
            root / "logs" / "local-audit-events.jsonl",
            {
                "schema_version": 2,
                "event_id": (
                    f"capability-advertisement:{action}:{validation_receipt_ref}:"
                    f"{capability_id}"
                ),
                "timestamp": timestamp,
                "event_type": "capability_advertised",
                "actor_node_id": node_id,
                "creator_node_id": creator_node_id,
                "local_run_id": f"local-startup:{validation_receipt_ref}",
                "event_sequence": event_sequence,
                "capability_advertisement_action": action,
                "node_id": node_id,
                "capability_id": capability_id,
                "manifest_ref": manifest_ref,
                "manifest_digest": manifest_hash,
                "advertisement_payload_digest": _document_hash(advertisement),
                "validation_status": "passed",
                "validation_receipt_refs": [required_receipt_ref],
                "lineage_refs": [lineage_ref],
                "contribution_attribution": {
                    "creator_node_id": creator_node_id,
                    "attribution_node_id": node_id,
                    "work_record_ref": work_record_ref,
                },
                "related_file_paths": [
                    manifest_ref,
                    required_receipt_ref,
                    validation_receipt_ref,
                    lineage_ref,
                    work_record_ref,
                ],
            },
        )


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
