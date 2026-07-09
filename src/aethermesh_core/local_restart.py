"""Local-first restart path for one developer AetherMesh node."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aethermesh_core.json_io import atomic_create_json
from aethermesh_core.local_json_helpers import (
    append_json_line,
    canonical_json_hash,
    load_json_mapping,
    require_text_field,
)
from aethermesh_core.local_shutdown import LocalShutdownError, shutdown_local_node
from aethermesh_core.local_startup import LocalStartupError, start_local_node

LOCAL_RESTART_RECEIPT_VERSION = 1


class LocalRestartError(ValueError):
    """Raised when local node restart cannot safely preserve persisted state."""


@dataclass(frozen=True)
class LocalRestartResult:
    """Serializable summary for one local-only node restart."""

    node_id: str
    creator_node_id: str
    manifest_path: str
    manifest_hash: str
    shutdown_state_path: str
    startup_receipt_path: str
    startup_lineage_path: str
    restart_receipt_path: str
    restored_manifest_refs: tuple[str, ...]
    restored_validation_receipt_refs: tuple[str, ...]
    restored_lineage_refs: tuple[str, ...]
    restored_contribution_refs: tuple[str, ...]
    recovery_decisions: tuple[dict[str, str], ...]
    final_status: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable restart summary with local-only refs."""

        return {
            "node_id": self.node_id,
            "creator_node_id": self.creator_node_id,
            "manifest_path": self.manifest_path,
            "manifest_hash": self.manifest_hash,
            "shutdown_state_path": self.shutdown_state_path,
            "startup_receipt_path": self.startup_receipt_path,
            "startup_lineage_path": self.startup_lineage_path,
            "restart_receipt_path": self.restart_receipt_path,
            "restored_manifest_refs": list(self.restored_manifest_refs),
            "restored_validation_receipt_refs": list(
                self.restored_validation_receipt_refs
            ),
            "restored_lineage_refs": list(self.restored_lineage_refs),
            "restored_contribution_refs": list(self.restored_contribution_refs),
            "recovery_decisions": [
                dict(decision) for decision in self.recovery_decisions
            ],
            "final_status": self.final_status,
            "network_mode": "local-only-no-p2p",
        }


def restart_local_node(
    runtime_dir: str | Path, *, timeout_seconds: float = 5.0
) -> LocalRestartResult:
    """Cleanly stop and start a local runtime from persisted local state.

    Restart recovery is intentionally local-only: it reuses persisted identity,
    validates restored local references are still readable, records interrupted
    work as pending retry, and never claims remote coordination.
    """

    root = Path(runtime_dir)
    timestamp = _now()
    try:
        shutdown = shutdown_local_node(root, timeout_seconds=timeout_seconds)
    except LocalShutdownError as exc:
        raise LocalRestartError(str(exc)) from exc

    shutdown_state = _load_json_object(root / shutdown.state_path, "shutdown state")
    previous_node_id = _required_string(shutdown_state, "node_id", "shutdown state")
    previous_creator_node_id = _required_string(
        shutdown_state, "creator_node_id", "shutdown state"
    )
    manifest_ref = _required_string(shutdown_state, "manifest_ref", "shutdown state")
    manifest = _load_json_object(root / manifest_ref, "manifest")
    restored_validation_receipt_refs = _load_ref_tuple(
        root, shutdown_state, "validation_receipt_refs", "validation receipt"
    )
    restored_lineage_refs = _load_ref_tuple(
        root, shutdown_state, "lineage_refs", "lineage record"
    )
    restored_contribution_refs = _load_ref_tuple(
        root, shutdown_state, "contribution_refs", "contribution record"
    )
    recovery_decisions = _recovery_decisions(root, shutdown_state)

    try:
        startup = start_local_node(root)
    except LocalStartupError as exc:
        raise LocalRestartError(str(exc)) from exc
    if startup.node_id != previous_node_id:
        raise LocalRestartError("restart changed node_id; refusing recovered runtime")
    if startup.creator_node_id != previous_creator_node_id:
        raise LocalRestartError(
            "restart changed creator_node_id; refusing recovered runtime"
        )

    restart_receipt_ref = _next_restart_receipt_ref(root, timestamp)
    restart_receipt_path = root / restart_receipt_ref
    receipt = {
        "version": LOCAL_RESTART_RECEIPT_VERSION,
        "receipt_type": "local_node_restart",
        "timestamp": timestamp,
        "node_id": startup.node_id,
        "creator_node_id": startup.creator_node_id,
        "previous_runtime_state": {
            "shutdown_state_ref": shutdown.state_path,
            "status": shutdown_state.get("status"),
            "interrupted_work_count": shutdown_state.get("interrupted_work_count", 0),
        },
        "restored_identity": {
            "node_id": startup.node_id,
            "creator_node_id": startup.creator_node_id,
            "identity_ref": startup.identity_path,
        },
        "restored_manifests": [manifest_ref],
        "restored_validation_receipts": list(restored_validation_receipt_refs),
        "restored_lineage": list(restored_lineage_refs),
        "restored_contribution_attribution": list(restored_contribution_refs),
        "recovery_decisions": [dict(decision) for decision in recovery_decisions],
        "new_startup_receipt_ref": startup.validation_receipt_path,
        "new_startup_lineage_ref": startup.lineage_path,
        "network_mode": "local-only-no-p2p",
    }
    try:
        atomic_create_json(restart_receipt_path, receipt)
        _append_log(
            root / "logs" / "restart.log",
            event="local_node_restart",
            timestamp=timestamp,
            node_id=startup.node_id,
            creator_node_id=startup.creator_node_id,
            restart_receipt_ref=restart_receipt_ref,
            recovery_decision_count=len(recovery_decisions),
            network_mode="local-only-no-p2p",
        )
    except OSError as exc:
        raise LocalRestartError(f"could not record restart receipt: {exc}") from exc

    return LocalRestartResult(
        node_id=startup.node_id,
        creator_node_id=startup.creator_node_id,
        manifest_path=manifest_ref,
        manifest_hash=_document_hash(manifest),
        shutdown_state_path=shutdown.state_path,
        startup_receipt_path=startup.validation_receipt_path,
        startup_lineage_path=startup.lineage_path,
        restart_receipt_path=restart_receipt_ref,
        restored_manifest_refs=(manifest_ref,),
        restored_validation_receipt_refs=restored_validation_receipt_refs,
        restored_lineage_refs=restored_lineage_refs,
        restored_contribution_refs=restored_contribution_refs,
        recovery_decisions=recovery_decisions,
        final_status="restarted",
    )


def _load_ref_tuple(
    root: Path, document: dict[str, Any], field_name: str, label: str
) -> tuple[str, ...]:
    value = document.get(field_name)
    if not isinstance(value, list) or any(not isinstance(ref, str) for ref in value):
        raise LocalRestartError(f"shutdown state {field_name} must be a list of refs")
    refs = tuple(value)
    for ref in refs:
        _load_json_object(root / ref, label)
    return refs


def _recovery_decisions(
    root: Path, shutdown_state: dict[str, Any]
) -> tuple[dict[str, str], ...]:
    stopped_ref = shutdown_state.get("interrupted_work_ref")
    if stopped_ref is None:
        return ()
    if not isinstance(stopped_ref, str) or not stopped_ref:
        raise LocalRestartError("shutdown state interrupted_work_ref must be a ref")
    stopped = _load_json_object(root / stopped_ref, "interrupted work")
    work = stopped.get("work")
    if not isinstance(work, list):
        raise LocalRestartError("interrupted work must contain a work list")
    decisions: list[dict[str, str]] = []
    for item in work:
        if not isinstance(item, dict):
            raise LocalRestartError("interrupted work entries must be objects")
        work_ref = item.get("work_ref")
        if not isinstance(work_ref, str) or not work_ref:
            raise LocalRestartError("interrupted work entry requires work_ref")
        decisions.append(
            {
                "work_ref": work_ref,
                "previous_status": str(item.get("status", "interrupted")),
                "restart_status": "pending_retry",
                "decision": "left pending for local retry; not marked completed or validated",
            }
        )
    return tuple(decisions)


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    return load_json_mapping(path, label, LocalRestartError)


def _required_string(document: dict[str, Any], field_name: str, label: str) -> str:
    return require_text_field(document, field_name, label, LocalRestartError)


def _next_restart_receipt_ref(root: Path, timestamp: str) -> str:
    directory = root / "receipts"
    directory.mkdir(parents=True, exist_ok=True)
    slug = timestamp.replace(":", "").replace("+", "Z")
    index = len(tuple(directory.glob("local-restart-*.json"))) + 1
    return f"receipts/local-restart-{slug}-{index:04d}.json"


def _append_log(path: Path, **payload: object) -> None:
    append_json_line(path, payload, create_parent=True)


def _document_hash(document: dict[str, Any]) -> str:
    return canonical_json_hash(document, prefix="sha256:")


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
