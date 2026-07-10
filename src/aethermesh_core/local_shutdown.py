"""Local-first graceful shutdown path for one developer AetherMesh node."""

from __future__ import annotations

import re
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


class LocalShutdownReportError(LocalShutdownError):
    """Concise terminal report for a shutdown failure; detail remains in local logs."""

    def __init__(
        self,
        *,
        code: str,
        component: str,
        node_id: str,
        artifact_path: str | None,
        contribution_records_finalized: bool,
        shutdown_state: str,
        detail: str,
        guidance: str,
    ) -> None:
        self.code = code
        self.component = component
        self.node_id = node_id
        self.artifact_path = artifact_path
        self.contribution_records_finalized = contribution_records_finalized
        self.shutdown_state = shutdown_state
        self.detail = detail
        self.guidance = guidance
        super().__init__(detail)

    def to_dict(self) -> dict[str, object]:
        """Return automation-safe shutdown fields without raw local details."""

        return {
            "summary": "Local node shutdown did not complete safely.",
            "code": self.code,
            "component": self.component,
            "node_id": self.node_id,
            "artifact_path": self.artifact_path,
            "contribution_records_finalized": self.contribution_records_finalized,
            "shutdown_state": self.shutdown_state,
            "guidance": self.guidance,
        }

    def __str__(self) -> str:
        artifact = f" artifact={self.artifact_path}" if self.artifact_path else ""
        return (
            f"[{self.code}] shutdown {self.shutdown_state}: {self.component} failed "
            f"for node={self.node_id}{artifact}; "
            f"contribution_records_finalized={self.contribution_records_finalized}. "
            f"Reason: {_redact_local_paths(self.detail)}. Safe next step: {self.guidance}"
        )


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
    shutdown_state: str

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
            "shutdown_state": self.shutdown_state,
            "accepting_work": False,
        }


def shutdown_local_node(
    runtime_dir: str | Path, *, timeout_seconds: float = 5.0
) -> LocalShutdownResult:
    """Persist final local state and mark one runtime stopped idempotently."""

    root = Path(runtime_dir)
    try:
        return _shutdown_local_node(root, timeout_seconds=timeout_seconds)
    except LocalShutdownReportError:
        raise
    except LocalShutdownError as exc:
        report = _shutdown_error_report(root, exc)
        _append_failure_log(root / "logs" / "shutdown.log", report)
        raise report from exc


def _shutdown_local_node(root: Path, *, timeout_seconds: float) -> LocalShutdownResult:
    """Perform shutdown; the public wrapper converts failures to stable reports."""

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
        _write_shutdown_json(
            stopped_work_path,
            {
                "version": LOCAL_SHUTDOWN_STATE_VERSION,
                "node_id": node_id,
                "creator_node_id": creator_node_id,
                "status": "stopped_retryable",
                "work": interrupted_work,
            },
            "interrupted work receipt",
            _relative_ref(root, stopped_work_path),
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
    _write_shutdown_json(
        state_path,
        final_state,
        "attribution finalization",
        _relative_ref(root, state_path),
    )
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
        shutdown_state=(
            "forced_shutdown"
            if final_state["bounded_timeout_reached"]
            else "clean_shutdown"
        ),
    )


def _shutdown_error_report(
    root: Path, error: LocalShutdownError
) -> LocalShutdownReportError:
    """Classify a failure without modifying any identity or contribution artifact."""

    detail = str(error)
    lowered = detail.lower()
    component, code, artifact_path, guidance = _shutdown_failure_fields(lowered)
    return LocalShutdownReportError(
        code=code,
        component=component,
        node_id=_shutdown_node_id(root),
        artifact_path=artifact_path,
        contribution_records_finalized=_contribution_records_finalized(root),
        shutdown_state=(
            "partial_shutdown"
            if _contribution_records_finalized(root)
            else "unsafe_incomplete_shutdown"
        ),
        detail=detail,
        guidance=guidance,
    )


def _shutdown_failure_fields(detail: str) -> tuple[str, str, str | None, str]:
    """Map known local shutdown phases to stable, actionable operator fields."""

    if "release runtime resource" in detail:
        return (
            "worker_termination",
            "SHUTDOWN_WORKER_TERMINATION_FAILED",
            "node.pid",
            "stop the named local worker, then rerun shutdown; do not delete identity or receipts",
        )
    if "interrupted work receipt" in detail:
        return (
            "receipt_write",
            "SHUTDOWN_RECEIPT_WRITE_FAILED",
            "work/stopped/shutdown-interrupted-work.json",
            "restore write access and rerun shutdown; existing validation receipts remain unchanged",
        )
    if "attribution finalization" in detail:
        return (
            "attribution_finalization",
            "SHUTDOWN_ATTRIBUTION_FINALIZATION_FAILED",
            "state/shutdown-state.json",
            "restore write access and rerun shutdown; do not treat contribution attribution as finalized",
        )
    if "manifest" in detail:
        return (
            "manifest_flush",
            "SHUTDOWN_MANIFEST_FLUSH_FAILED",
            "manifests/local-node-manifest.json",
            "restore the preserved manifest and rerun shutdown; do not replace node identity",
        )
    if "identity" in detail:
        return (
            "runtime_stop",
            "SHUTDOWN_IDENTITY_UNAVAILABLE",
            "identity/local-node-identity.json",
            "restore readable local identity, then rerun shutdown without resetting creator identity",
        )
    return (
        "runtime_stop",
        "SHUTDOWN_RUNTIME_STOP_FAILED",
        None,
        "resolve the local runtime error and rerun shutdown; preserve identity and artifacts",
    )


def _shutdown_node_id(root: Path) -> str:
    try:
        config = load_optional_local_runtime_config(root, LocalShutdownError)
        identity_path = configured_runtime_path(root, config, "identity")
        identity = _load_json_object(identity_path, "identity")
        node = _required_object(identity, "node", "identity")
        return _required_string(node, "node_id", "identity.node")
    except LocalShutdownError:
        return "unknown-local-node"


def _contribution_records_finalized(root: Path) -> bool:
    try:
        state = _load_json_object(
            root / "state" / "shutdown-state.json", "shutdown state"
        )
    except LocalShutdownError:
        return False
    return state.get("status") == "stopped" and isinstance(
        state.get("contribution_refs"), list
    )


def _append_failure_log(path: Path, report: LocalShutdownReportError) -> None:
    """Keep raw diagnostic detail local; terminal output uses report.__str__ instead."""

    try:
        append_json_line(
            path,
            {
                "event": "shutdown_failure",
                **report.to_dict(),
                "error_detail": report.detail,
            },
            create_parent=True,
        )
    except OSError:
        return


def _write_shutdown_json(
    path: Path, document: dict[str, object], component: str, artifact_path: str
) -> None:
    try:
        atomic_write_json(path, document)
    except (OSError, TypeError, ValueError) as exc:
        raise LocalShutdownError(
            f"{component} failed for {artifact_path}: {exc}"
        ) from exc


def _redact_local_paths(detail: str) -> str:
    """Retain diagnostic context in a local log without persisting host paths."""

    return re.sub(r"(?<![\w.])(?:[A-Za-z]:[\\/]|/)[^\s'\"]+", "<local-path>", detail)


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
                f"could not release runtime resource {path.name}: {exc}"
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
