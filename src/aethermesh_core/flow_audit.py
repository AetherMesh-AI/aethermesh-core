"""Read-only audit checks for completed local flow artifact directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, TypeVar
from urllib.parse import quote

from aethermesh_core.ledger import load_existing_ledger_document
from aethermesh_core.message_log import (
    load_message_log_document,
    load_message_log_messages,
    load_worker_emitted_messages,
)
from aethermesh_core.node_state import load_node_processing_state
from aethermesh_core.receipts import load_receipt_document_if_exists


class FlowAuditError(ValueError):
    """Raised when local flow artifacts are missing or internally inconsistent."""


_T = TypeVar("_T")


def audit_local_flow(output_dir: str | Path) -> dict[str, Any]:
    """Audit a completed ``run-local-flow`` artifact directory without writing files."""

    output_path = Path(output_dir)
    dispatch_message_log_path = output_path / "dispatch-message-log.json"
    flow_message_log_path = output_path / "flow-message-log.json"
    ledger_path = output_path / "ledger.json"
    receipts_path = output_path / "receipts.json"
    worker_log_dir = output_path / "worker-message-logs"
    node_state_dir = output_path / "node-state"

    dispatch_document = _load_or_audit_error(
        "dispatch message log",
        lambda: load_message_log_document(dispatch_message_log_path),
    )
    flow_document = _load_or_audit_error(
        "flow message log",
        lambda: load_message_log_document(flow_message_log_path),
    )
    dispatch_messages = _load_or_audit_error(
        "dispatch message log",
        lambda: load_message_log_messages(dispatch_message_log_path),
    )
    flow_messages = _load_or_audit_error(
        "flow message log",
        lambda: load_message_log_messages(flow_message_log_path),
    )
    ledger, _extra_fields = _load_or_audit_error(
        "ledger",
        lambda: load_existing_ledger_document(ledger_path),
    )
    receipt_document = _load_or_audit_error(
        "receipts",
        lambda: load_receipt_document_if_exists(receipts_path),
    )
    if receipt_document is None:
        raise FlowAuditError(f"receipt file does not exist: {receipts_path}")

    dispatch_metadata = _metadata(dispatch_document, "dispatch message log")
    flow_metadata = _metadata(flow_document, "flow message log")
    _require_metadata_value(
        dispatch_metadata,
        "message_count",
        len(dispatch_messages),
        "dispatch message log",
    )
    _require_metadata_value(
        flow_metadata,
        "message_count",
        len(flow_messages),
        "flow message log",
    )
    _require_metadata_value(
        flow_metadata,
        "dispatch_message_count",
        len(dispatch_messages),
        "flow message log",
    )

    dispatch_assignment_ids = {
        message.message_id
        for message in dispatch_messages
        if message.message_type == "job_assigned"
    }
    dispatch_assignment_nodes = {
        message.message_id: message.recipient_node_id
        for message in dispatch_messages
        if message.message_type == "job_assigned"
    }
    flow_message_ids = {message.message_id for message in flow_messages}

    worker_paths_by_node = _worker_paths_from_metadata(flow_metadata, worker_log_dir)
    emitted_worker_messages_by_id: dict[str, Any] = {}
    emitted_worker_message_count = 0
    for node_id, worker_path in worker_paths_by_node.items():
        emitted_messages = _load_or_audit_error(
            f"worker message log for node {node_id}",
            lambda worker_path=worker_path: load_worker_emitted_messages(worker_path),
        )
        emitted_worker_message_count += len(emitted_messages)
        for message in emitted_messages:
            emitted_worker_messages_by_id[message.message_id] = message
    _require_metadata_value(
        flow_metadata,
        "emitted_message_count",
        emitted_worker_message_count,
        "flow message log",
    )

    receipts = receipt_document["receipts"]
    receipt_node_ids = sorted({str(receipt["node_id"]) for receipt in receipts})
    node_state_paths_by_node = _load_node_states(
        node_state_dir=node_state_dir,
        worker_node_ids=sorted(worker_paths_by_node),
        receipt_node_ids=receipt_node_ids,
    )
    node_states = {
        node_id: _load_or_audit_error(
            f"node-state file for node {node_id}",
            lambda node_id=node_id, state_path=state_path: load_node_processing_state(
                state_path, expected_node_id=node_id
            ),
        )
        for node_id, state_path in node_state_paths_by_node.items()
    }

    for index, receipt in enumerate(receipts):
        assignment_message_id = receipt["assignment_message_id"]
        if assignment_message_id not in dispatch_assignment_ids:
            raise FlowAuditError(
                f"receipt entry {index} assignment_message_id not found in dispatch log: {assignment_message_id}"
            )
        node_id = receipt["node_id"]
        if dispatch_assignment_nodes.get(assignment_message_id) != node_id:
            raise FlowAuditError(
                f"receipt entry {index} node_id does not match dispatch assignment recipient: {node_id}"
            )
        if node_id not in node_states:
            raise FlowAuditError(
                f"receipt entry {index} node_id not represented in node-state files: {node_id}"
            )
        if assignment_message_id not in node_states[node_id].processed_message_ids:
            raise FlowAuditError(
                f"node-state for node {node_id} does not include receipt assignment_message_id: {assignment_message_id}"
            )
        result_message_id = receipt["result_message_id"]
        if result_message_id not in flow_message_ids:
            raise FlowAuditError(
                f"receipt entry {index} result_message_id not found in flow log: {result_message_id}"
            )
        result_message = emitted_worker_messages_by_id.get(result_message_id)
        if result_message is None or result_message.message_type != "job_result_reported":
            raise FlowAuditError(
                f"receipt entry {index} result_message_id not found in emitted worker result messages: {result_message_id}"
            )
        contribution_message_id = receipt.get("contribution_message_id")
        if not isinstance(contribution_message_id, str) or contribution_message_id == "":
            raise FlowAuditError(
                f"receipt entry {index} contribution_message_id must be present"
            )
        if contribution_message_id not in flow_message_ids:
            raise FlowAuditError(
                f"receipt entry {index} contribution_message_id not found in flow log: {contribution_message_id}"
            )
        contribution_message = emitted_worker_messages_by_id.get(contribution_message_id)
        if (
            contribution_message is None
            or contribution_message.message_type != "contribution_recorded"
        ):
            raise FlowAuditError(
                f"receipt entry {index} contribution_message_id not found in emitted worker contribution messages: {contribution_message_id}"
            )

    ledger_summary = ledger.summary_document(ledger_path)
    ledger_record_count = int(ledger_summary["record_count"])
    if ledger_record_count != len(receipts):
        raise FlowAuditError(
            "ledger record count does not match receipt count: "
            f"ledger={ledger_record_count} receipts={len(receipts)}"
        )
    ledger_total_units = int(ledger_summary["total_contribution_units"])
    credited_receipt_units = sum(int(receipt["credited_units"]) for receipt in receipts)
    if credited_receipt_units != ledger_total_units:
        raise FlowAuditError(
            "receipt credited units do not match ledger total contribution units: "
            f"receipts={credited_receipt_units} ledger={ledger_total_units}"
        )

    processed_assignment_count = sum(
        state.processed_assignment_count for state in node_states.values()
    )
    _require_metadata_value(
        flow_metadata,
        "processed_assignment_count",
        processed_assignment_count,
        "flow message log",
    )
    skipped_processed_assignment_count = _int_metadata_value(
        flow_metadata,
        "skipped_processed_assignment_count",
        "flow message log",
    )

    audited_node_ids = sorted(node_states)
    return {
        "ok": True,
        "output_dir": str(output_path),
        "artifacts": {
            "dispatch_message_log": str(dispatch_message_log_path),
            "flow_message_log": str(flow_message_log_path),
            "ledger": str(ledger_path),
            "receipts": str(receipts_path),
            "worker_message_logs": [
                str(worker_paths_by_node[node_id]) for node_id in sorted(worker_paths_by_node)
            ],
            "node_state_files": [
                str(node_state_paths_by_node[node_id])
                for node_id in sorted(node_state_paths_by_node)
            ],
        },
        "dispatch_message_count": len(dispatch_messages),
        "flow_message_count": len(flow_messages),
        "emitted_worker_message_count": emitted_worker_message_count,
        "receipt_count": len(receipts),
        "ledger_record_count": ledger_record_count,
        "processed_assignment_count": processed_assignment_count,
        "skipped_processed_assignment_count": skipped_processed_assignment_count,
        "total_contribution_units": ledger_total_units,
        "credited_receipt_units": credited_receipt_units,
        "audited_node_ids": audited_node_ids,
        "processed_node_ids": sorted(_list_metadata_value(flow_metadata, "processed_node_ids")),
    }


def _load_or_audit_error(label: str, loader: Callable[[], _T]) -> _T:
    try:
        return loader()
    except FlowAuditError:
        raise
    except ValueError as exc:
        raise FlowAuditError(f"{label} is invalid: {exc}") from exc


def _metadata(document: dict[str, Any], label: str) -> dict[str, Any]:
    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        raise FlowAuditError(f"{label} metadata must be an object")
    return metadata


def _int_metadata_value(metadata: dict[str, Any], field_name: str, label: str) -> int:
    value = metadata.get(field_name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise FlowAuditError(f"{label} metadata field '{field_name}' must be an integer")
    return value


def _require_metadata_value(
    metadata: dict[str, Any], field_name: str, expected: int, label: str
) -> None:
    actual = _int_metadata_value(metadata, field_name, label)
    if actual != expected:
        raise FlowAuditError(
            f"{label} metadata field '{field_name}' mismatch: expected {expected} found {actual}"
        )


def _list_metadata_value(metadata: dict[str, Any], field_name: str) -> list[str]:
    value = metadata.get(field_name)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise FlowAuditError(f"flow message log metadata field '{field_name}' must be a string list")
    return list(value)


def _worker_paths_from_metadata(
    flow_metadata: dict[str, Any], worker_log_dir: Path
) -> dict[str, Path]:
    raw_paths = flow_metadata.get("worker_message_log_paths")
    if not isinstance(raw_paths, dict):
        raise FlowAuditError(
            "flow message log metadata field 'worker_message_log_paths' must be an object"
        )
    worker_paths: dict[str, Path] = {}
    for node_id in sorted(raw_paths):
        raw_path = raw_paths[node_id]
        if not isinstance(node_id, str) or node_id == "":
            raise FlowAuditError("worker message log path node ids must be non-empty strings")
        if not isinstance(raw_path, str) or raw_path == "":
            raise FlowAuditError(
                f"worker message log path for node {node_id} must be a non-empty string"
            )
        worker_path = Path(raw_path)
        if worker_path.parent.resolve() != worker_log_dir.resolve():
            raise FlowAuditError(
                f"worker message log for node {node_id} is not under {worker_log_dir}: {worker_path}"
            )
        if not worker_path.exists():
            raise FlowAuditError(
                f"worker message log for node {node_id} does not exist: {worker_path}"
            )
        worker_paths[node_id] = worker_path
    return worker_paths


def _load_node_states(
    *, node_state_dir: Path, worker_node_ids: list[str], receipt_node_ids: list[str]
) -> dict[str, Path]:
    required_node_ids = sorted(set(worker_node_ids).union(receipt_node_ids))
    state_paths: dict[str, Path] = {}
    for node_id in required_node_ids:
        state_path = node_state_dir / f"{quote(node_id, safe='-._~')}.json"
        if not state_path.exists():
            raise FlowAuditError(f"node-state file for node {node_id} does not exist: {state_path}")
        state_paths[node_id] = state_path
    return state_paths
