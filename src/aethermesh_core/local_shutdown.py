"""Local-first graceful shutdown path for one developer AetherMesh node."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from aethermesh_core.json_io import atomic_write_json

LOCAL_SHUTDOWN_STATE_VERSION = 1


class LocalShutdownError(ValueError):
    """Raised when local node shutdown cannot preserve required state."""


@dataclass(frozen=True)
class LocalShutdownResult:
    """Serializable summary for one local node shutdown request."""

    node_id: str
    creator_node_id: str
    manifest_path: str
    manifest_hash: str
    state_path: str
    stopped_work_path: str | None
    log_path: str
    validation_receipt_count: int
    lineage_record_count: int
    contribution_record_count: int
    interrupted_work_count: int
    repeated_request: bool
    final_status: str

    def to_dict(self) -> dict[str, object]:
        """Return the local shutdown summary without host-specific absolute paths."""

        return {
            "node_id": self.node_id,
            "creator_node_id": self.creator_node_id,
            "manifest_path": self.manifest_path,
            "manifest_hash": self.manifest_hash,
            "state_path": self.state_path,
            "stopped_work_path": self.stopped_work_path,
            "log_path": self.log_path,
            "validation_receipt_count": self.validation_receipt_count,
            "lineage_record_count": self.lineage_record_count,
            "contribution_record_count": self.contribution_record_count,
            "interrupted_work_count": self.interrupted_work_count,
            "repeated_request": self.repeated_request,
            "final_status": self.final_status,
            "accepting_work": False,
        }


def shutdown_local_node(
    runtime_dir: str | Path, *, timeout_seconds: float = 5.0
) -> LocalShutdownResult:
    """Persist final local state and mark one runtime stopped idempotently."""

    if timeout_seconds < 0:
        raise LocalShutdownError("shutdown timeout must be non-negative")
    root = Path(runtime_dir)
    identity_path = root / "identity" / "creator-node.json"
    manifest_path = root / "manifests" / "local-node-manifest.json"
    log_path = root / "logs" / "shutdown.log"
    state_dir = root / "state"
    state_path = state_dir / "shutdown-state.json"
    stopped_work_path = root / "work" / "stopped" / "shutdown-interrupted-work.json"
    pid_path = root / "node.pid"
    lock_path = root / "runtime.lock"

    started_at = _now()
    deadline = time.monotonic() + timeout_seconds
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    repeated_request = _shutdown_already_completed(state_path)
    _append_log(
        log_path,
        event="shutdown_start",
        timestamp=started_at,
        repeated_request=repeated_request,
        accepting_work=False,
    )

    identity = _load_json_object(identity_path, "identity")
    manifest = _load_json_object(manifest_path, "manifest")
    identity_node = _required_object(identity, "node", "identity")
    manifest_node = _required_object(manifest, "node", "manifest")
    node_id = _required_string(identity_node, "node_id", "identity.node")
    creator_node_id = _required_string(
        identity_node, "creator_node_id", "identity.node"
    )
    manifest_node_id = _required_string(manifest_node, "node_id", "manifest.node")
    manifest_creator_node_id = _required_string(
        manifest_node, "creator_node_id", "manifest.node"
    )
    if manifest_node_id != node_id or manifest_creator_node_id != creator_node_id:
        raise LocalShutdownError(
            "shutdown refused because identity and manifest node references differ"
        )

    interrupted_work = _interrupted_work_refs(root)
    stopped_work_ref = None
    if interrupted_work:
        stopped_work_path.parent.mkdir(parents=True, exist_ok=True)
        stopped_work_ref = _relative_ref(root, stopped_work_path)
        atomic_write_json(
            stopped_work_path,
            {
                "version": LOCAL_SHUTDOWN_STATE_VERSION,
                "node_id": node_id,
                "creator_node_id": creator_node_id,
                "status": "stopped_retryable",
                "work": interrupted_work,
            },
        )

    receipt_refs = _artifact_refs(root, "receipts")
    lineage_refs = _artifact_refs(root, "lineage")
    contribution_refs = _artifact_refs(root, "contributions")
    final_state = {
        "version": LOCAL_SHUTDOWN_STATE_VERSION,
        "node_id": node_id,
        "creator_node_id": creator_node_id,
        "status": "stopped",
        "accepting_work": False,
        "manifest_ref": _relative_ref(root, manifest_path),
        "manifest_hash": _document_hash(manifest),
        "validation_receipt_refs": receipt_refs,
        "lineage_refs": lineage_refs,
        "contribution_refs": contribution_refs,
        "interrupted_work_ref": stopped_work_ref,
        "interrupted_work_count": len(interrupted_work),
        "shutdown_started_at": started_at,
        "shutdown_timeout_seconds": timeout_seconds,
        "bounded_timeout_reached": time.monotonic() > deadline,
    }
    atomic_write_json(state_path, final_state)
    _append_log(
        log_path,
        event="shutdown_persistence_complete",
        timestamp=_now(),
        validation_receipt_count=len(receipt_refs),
        lineage_record_count=len(lineage_refs),
        contribution_record_count=len(contribution_refs),
        interrupted_work_count=len(interrupted_work),
    )

    released = _release_runtime_resources(pid_path, lock_path)
    _append_log(
        log_path,
        event="shutdown_resources_released",
        timestamp=_now(),
        released_resources=released,
    )
    _append_log(
        log_path,
        event="shutdown_complete",
        timestamp=_now(),
        final_status="stopped",
    )

    return LocalShutdownResult(
        node_id=node_id,
        creator_node_id=creator_node_id,
        manifest_path=_relative_ref(root, manifest_path),
        manifest_hash=str(final_state["manifest_hash"]),
        state_path=_relative_ref(root, state_path),
        stopped_work_path=stopped_work_ref,
        log_path=_relative_ref(root, log_path),
        validation_receipt_count=len(receipt_refs),
        lineage_record_count=len(lineage_refs),
        contribution_record_count=len(contribution_refs),
        interrupted_work_count=len(interrupted_work),
        repeated_request=repeated_request,
        final_status="stopped",
    )


def _shutdown_already_completed(path: Path) -> bool:
    try:
        document = _load_json_object(path, "shutdown state")
    except LocalShutdownError:
        return False
    return document.get("status") == "stopped"


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except FileNotFoundError as exc:
        raise LocalShutdownError(f"required {label} file is missing") from exc
    except json.JSONDecodeError as exc:
        raise LocalShutdownError(f"{label} JSON is malformed: {exc.msg}") from exc
    except OSError as exc:
        raise LocalShutdownError(f"could not read {label} file: {exc}") from exc
    if not isinstance(document, dict):
        raise LocalShutdownError(f"{label} JSON must be an object")
    return document


def _required_string(document: dict[str, Any], field_name: str, label: str) -> str:
    value = document.get(field_name)
    if not isinstance(value, str) or not value:
        raise LocalShutdownError(f"{label} field {field_name!r} must be a string")
    return value


def _required_object(
    document: dict[str, Any], field_name: str, label: str
) -> dict[str, Any]:
    value = document.get(field_name)
    if not isinstance(value, dict):
        raise LocalShutdownError(f"{label} field {field_name!r} must be an object")
    return value


def _interrupted_work_refs(root: Path) -> list[dict[str, str]]:
    in_progress_dir = root / "work" / "in-progress"
    inputs_dir = root / "work" / "inputs"
    outputs_dir = root / "work" / "outputs"
    interrupted: list[dict[str, str]] = []
    for path in sorted(_iter_files(in_progress_dir)):
        interrupted.append(
            {"work_ref": _relative_ref(root, path), "status": "stopped_retryable"}
        )
    for path in sorted(_iter_files(inputs_dir)):
        if (outputs_dir / path.name).exists():
            continue
        interrupted.append(
            {"work_ref": _relative_ref(root, path), "status": "stopped_retryable"}
        )
    return interrupted


def _artifact_refs(root: Path, directory_name: str) -> list[str]:
    return [
        _relative_ref(root, path)
        for path in sorted(_iter_files(root / directory_name))
        if path.suffix == ".json"
    ]


def _iter_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return [path for path in directory.iterdir() if path.is_file()]


def _release_runtime_resources(*paths: Path) -> list[str]:
    released: list[str] = []
    for path in paths:
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise LocalShutdownError(
                f"could not release runtime resource: {exc}"
            ) from exc
        released.append(path.name)
    return released


def _append_log(path: Path, **payload: object) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True))
        handle.write("\n")


def _document_hash(document: dict[str, Any]) -> str:
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return sha256(canonical).hexdigest()


def _relative_ref(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise LocalShutdownError(
            "shutdown artifacts must stay inside runtime dir"
        ) from exc


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
