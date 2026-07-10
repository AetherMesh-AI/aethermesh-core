"""Local-first graceful shutdown path for one developer AetherMesh node."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aethermesh_core.json_io import atomic_write_json
from aethermesh_core.local_json_helpers import (
    append_json_line,
    canonical_json_hash,
    load_json_mapping,
    require_text_field,
)
from aethermesh_core.local_runtime_config import (
    LocalRuntimeConfig,
    configured_runtime_path,
    configured_runtime_ref,
    load_optional_local_runtime_config,
)

LOCAL_SHUTDOWN_STATE_VERSION = 1


class LocalShutdownError(ValueError):
    """Raised when local node shutdown cannot preserve required state."""

    def __init__(
        self, message: str, *, report: "LocalShutdownFailure | None" = None
    ) -> None:
        super().__init__(message)
        self.report = report


@dataclass(frozen=True)
class LocalShutdownFailure:
    """Safe operator-facing description of an incomplete local shutdown."""

    code: str
    component: str
    node_id: str | None
    artifact_path: str | None
    worker_name: str | None
    contribution_records_finalized: bool
    shutdown_state: str
    next_action: str

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": "Local node shutdown did not complete cleanly.",
            "code": self.code,
            "component": self.component,
            "node_id": self.node_id,
            "artifact_path": self.artifact_path,
            "worker_name": self.worker_name,
            "contribution_records_finalized": self.contribution_records_finalized,
            "shutdown_state": self.shutdown_state,
            "next_action": self.next_action,
        }


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

    root = Path(runtime_dir)
    try:
        return _shutdown_local_node(root, timeout_seconds=timeout_seconds)
    except LocalShutdownError as exc:
        if exc.report is not None:
            raise
        raise _shutdown_failure(root, exc) from exc
    except Exception as exc:
        raise _shutdown_failure(root, exc) from exc


def _shutdown_local_node(
    root: Path, *, timeout_seconds: float = 5.0
) -> LocalShutdownResult:
    """Perform the shutdown; the public entry point formats unexpected failures."""

    if timeout_seconds < 0:
        raise LocalShutdownError("shutdown timeout must be non-negative")
    config = load_optional_local_runtime_config(root, LocalShutdownError)
    identity_path = configured_runtime_path(root, config, "identity")
    manifest_path = configured_runtime_path(root, config, "manifest")
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

    interrupted_work = _interrupted_work_refs(root, config)
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

    receipt_refs = _artifact_refs(
        root, configured_runtime_ref(config, "validation_receipts")
    )
    lineage_refs = _artifact_refs(root, configured_runtime_ref(config, "lineage"))
    contribution_refs = _artifact_refs(
        root, configured_runtime_ref(config, "contribution_attribution")
    )
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
    return load_json_mapping(path, label, LocalShutdownError)


def _required_string(document: dict[str, Any], field_name: str, label: str) -> str:
    return require_text_field(document, field_name, label, LocalShutdownError)


def _required_object(
    document: dict[str, Any], field_name: str, label: str
) -> dict[str, Any]:
    value = document.get(field_name)
    if not isinstance(value, dict):
        raise LocalShutdownError(f"{label} field {field_name!r} must be an object")
    return value


def _interrupted_work_refs(
    root: Path, config: LocalRuntimeConfig | None
) -> list[dict[str, str]]:
    in_progress_dir = root / "work" / "in-progress"
    inputs_dir = configured_runtime_path(root, config, "work_inputs")
    outputs_dir = configured_runtime_path(root, config, "work_outputs")
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
    append_json_line(path, payload)


def _document_hash(document: dict[str, Any]) -> str:
    return canonical_json_hash(document)


def _relative_ref(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:
        raise LocalShutdownError(
            "shutdown artifacts must stay inside runtime dir"
        ) from exc


def _shutdown_failure(root: Path, cause: Exception) -> LocalShutdownError:
    """Create a stable, path-safe failure report without altering audit artifacts."""

    detail = str(cause).lower()
    node_id = _failure_node_id(root)
    component = "attribution_finalization"
    code = "SHUTDOWN_ATTRIBUTION_FINALIZATION_FAILED"
    artifact_path: str | None = "state/shutdown-state.json"
    worker_name: str | None = None
    finalized = False
    state = "unsafe_incomplete"
    next_action = (
        "Keep existing artifacts, inspect the local shutdown log, then retry shutdown."
    )
    if "timeout" in detail:
        component = "signal_handling"
        code = "SHUTDOWN_SIGNAL_HANDLING_FAILED"
        artifact_path = None
        next_action = (
            "Keep the runtime running, resolve the signal timeout, then retry shutdown."
        )
    elif "release runtime resource" in detail:
        component = "worker_termination"
        code = "SHUTDOWN_WORKER_TERMINATION_FAILED"
        artifact_path = None
        worker_name = "node.pid"
        finalized = (root / "state" / "shutdown-state.json").is_file()
        state = "partial_shutdown" if finalized else "unsafe_incomplete"
        next_action = (
            "Confirm the named local worker has stopped before retrying shutdown."
        )
    elif "receipt" in detail:
        component = "receipt_write"
        code = "SHUTDOWN_RECEIPT_WRITE_FAILED"
        artifact_path = "receipts"
        next_action = "Keep existing receipts unchanged, repair receipt storage, then retry shutdown."
    elif "manifest" in detail:
        component = "manifest_flush"
        code = "SHUTDOWN_MANIFEST_FLUSH_FAILED"
        artifact_path = "manifests/local-node-manifest.json"
        next_action = "Keep the manifest unchanged, repair it or its storage, then retry shutdown."

    report = LocalShutdownFailure(
        code=code,
        component=component,
        node_id=node_id,
        artifact_path=artifact_path,
        worker_name=worker_name,
        contribution_records_finalized=finalized,
        shutdown_state=state,
        next_action=next_action,
    )
    _append_failure_log(root / "logs" / "shutdown.log", report, cause)
    return LocalShutdownError(f"{report.code}: {cause}", report=report)


def _failure_node_id(root: Path) -> str | None:
    """Best-effort identity lookup for an error report; never masks the original failure."""

    try:
        identity = _load_json_object(
            root / "identity" / "creator-node.json", "identity"
        )
        node = _required_object(identity, "node", "identity")
        return _required_string(node, "node_id", "identity.node")
    except (LocalShutdownError, OSError):
        return None


def _append_failure_log(
    log_path: Path, report: LocalShutdownFailure, cause: Exception
) -> None:
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _append_log(
            log_path,
            event="shutdown_failure",
            **report.to_dict(),
            error_detail=repr(cause),
        )
    except OSError:
        # Error reporting must not replace a shutdown failure with a logging failure.
        pass


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
