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
        self,
        summary: str,
        *,
        detail: str | None = None,
        error_code: str = "SHUTDOWN_RUNTIME_STOP_FAILED",
        failing_component: str = "runtime_stop",
        node_id: str | None = None,
        affected_artifact: str | None = None,
        contribution_records_finalized: bool = False,
        shutdown_outcome: str = "unsafe_incomplete",
    ) -> None:
        self.summary = summary
        self.detail = detail
        super().__init__(f"{summary} {detail}" if detail else summary)
        self.error_code = error_code
        self.failing_component = failing_component
        self.node_id = node_id
        self.affected_artifact = affected_artifact
        self.contribution_records_finalized = contribution_records_finalized
        self.shutdown_outcome = shutdown_outcome

    def to_dict(self) -> dict[str, object]:
        """Return a concise, path-safe shutdown failure report for operators."""

        return {
            "summary": self.summary,
            "error_code": self.error_code,
            "failing_component": self.failing_component,
            "node_id": self.node_id,
            "affected_artifact": self.affected_artifact,
            "contribution_records_finalized": self.contribution_records_finalized,
            "shutdown_outcome": self.shutdown_outcome,
            "next_action": (
                "Keep local artifacts intact, inspect logs/shutdown.log, resolve the "
                "reported component, then retry shutdown."
            ),
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
    shutdown_outcome: str

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
            "shutdown_outcome": self.shutdown_outcome,
            "accepting_work": False,
        }


def shutdown_local_node(
    runtime_dir: str | Path, *, timeout_seconds: float = 5.0
) -> LocalShutdownResult:
    """Persist final local state and mark one runtime stopped idempotently."""

    root = Path(runtime_dir)
    progress: dict[str, object] = {
        "component": "runtime_stop",
        "node_id": None,
        "artifact": None,
        "contribution_records_finalized": False,
    }
    try:
        return _shutdown_local_node(
            root, timeout_seconds=timeout_seconds, progress=progress
        )
    except (LocalShutdownError, OSError) as exc:
        raise _structured_shutdown_error(root, progress, exc) from exc


def _shutdown_local_node(
    root: Path, *, timeout_seconds: float, progress: dict[str, object]
) -> LocalShutdownResult:
    """Perform shutdown while retaining enough context for a safe error report."""

    if timeout_seconds < 0:
        raise LocalShutdownError("shutdown timeout must be non-negative")
    config = load_optional_local_runtime_config(root, LocalShutdownError)
    identity_path = configured_runtime_path(root, config, "identity")
    manifest_path = configured_runtime_path(root, config, "manifest")
    progress["artifact"] = _relative_ref(root, manifest_path)
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
    progress["component"] = "manifest_flush"
    manifest = _load_json_object(manifest_path, "manifest")
    identity_node = _required_object(identity, "node", "identity")
    manifest_node = _required_object(manifest, "node", "manifest")
    node_id = _required_string(identity_node, "node_id", "identity.node")
    creator_node_id = _required_string(
        identity_node, "creator_node_id", "identity.node"
    )
    progress["node_id"] = node_id
    manifest_node_id = _required_string(manifest_node, "node_id", "manifest.node")
    manifest_creator_node_id = _required_string(
        manifest_node, "creator_node_id", "manifest.node"
    )
    if manifest_node_id != node_id or manifest_creator_node_id != creator_node_id:
        raise LocalShutdownError(
            "shutdown refused because identity and manifest node references differ"
        )

    progress["component"] = "worker_termination"
    interrupted_work = _interrupted_work_refs(root, config)
    stopped_work_ref = None
    if interrupted_work:
        stopped_work_path.parent.mkdir(parents=True, exist_ok=True)
        stopped_work_ref = _relative_ref(root, stopped_work_path)
        progress["artifact"] = stopped_work_ref
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

    progress["component"] = "attribution_finalization"
    progress["artifact"] = configured_runtime_ref(config, "validation_receipts")
    receipt_refs = _artifact_refs(
        root, configured_runtime_ref(config, "validation_receipts")
    )
    progress["artifact"] = configured_runtime_ref(config, "lineage")
    lineage_refs = _artifact_refs(root, configured_runtime_ref(config, "lineage"))
    progress["artifact"] = configured_runtime_ref(config, "contribution_attribution")
    contribution_refs = _artifact_refs(
        root, configured_runtime_ref(config, "contribution_attribution")
    )
    shutdown_outcome = "forced" if time.monotonic() > deadline else "clean"
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
        "bounded_timeout_reached": shutdown_outcome == "forced",
        "shutdown_outcome": shutdown_outcome,
    }
    progress["component"] = "manifest_flush"
    progress["artifact"] = _relative_ref(root, state_path)
    atomic_write_json(state_path, final_state)
    progress["contribution_records_finalized"] = True
    _append_log(
        log_path,
        event="shutdown_persistence_complete",
        timestamp=_now(),
        validation_receipt_count=len(receipt_refs),
        lineage_record_count=len(lineage_refs),
        contribution_record_count=len(contribution_refs),
        interrupted_work_count=len(interrupted_work),
    )

    progress["component"] = "worker_termination"
    progress["artifact"] = _relative_ref(root, pid_path)
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
        shutdown_outcome=shutdown_outcome,
    )


def _structured_shutdown_error(
    root: Path, progress: dict[str, object], error: Exception
) -> LocalShutdownError:
    component = str(progress["component"])
    node_id = progress["node_id"]
    artifact = progress["artifact"]
    contribution_records_finalized = bool(progress["contribution_records_finalized"])
    error_code = {
        "runtime_stop": "SHUTDOWN_RUNTIME_STOP_FAILED",
        "manifest_flush": "SHUTDOWN_MANIFEST_FLUSH_FAILED",
        "worker_termination": "SHUTDOWN_WORKER_TERMINATION_FAILED",
        "attribution_finalization": "SHUTDOWN_ATTRIBUTION_FINALIZATION_FAILED",
    }[component]
    shutdown_outcome = (
        "partial_shutdown" if contribution_records_finalized else "unsafe_incomplete"
    )
    _record_shutdown_error(
        root,
        error_code=error_code,
        failing_component=component,
        node_id=node_id if isinstance(node_id, str) else None,
        affected_artifact=artifact if isinstance(artifact, str) else None,
        contribution_records_finalized=contribution_records_finalized,
        shutdown_outcome=shutdown_outcome,
        original_error=str(error),
    )
    return LocalShutdownError(
        f"Local shutdown incomplete while finalizing {component}.",
        detail=str(error),
        error_code=error_code,
        failing_component=component,
        node_id=node_id if isinstance(node_id, str) else None,
        affected_artifact=artifact if isinstance(artifact, str) else None,
        contribution_records_finalized=contribution_records_finalized,
        shutdown_outcome=shutdown_outcome,
    )


def _record_shutdown_error(root: Path, **payload: object) -> None:
    try:
        _append_log(root / "logs" / "shutdown.log", event="shutdown_error", **payload)
    except OSError:
        pass


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


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
