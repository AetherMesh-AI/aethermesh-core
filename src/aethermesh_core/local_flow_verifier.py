"""Read-only verification for local flow artifact directories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from aethermesh_core.ledger import LedgerPersistenceError, load_existing_ledger_document
from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    load_message_log_messages,
    load_worker_emitted_messages,
)
from aethermesh_core.node_state import NodeStatePersistenceError, load_node_processing_state
from aethermesh_core.receipts import ReceiptPersistenceError, load_receipt_document_if_exists

_EXPECTED_WORKER_MESSAGE_TYPES = {"job_result_reported", "contribution_recorded"}


def verify_local_flow(output_dir: str | Path) -> dict[str, object]:
    """Validate an existing ``run-local-flow`` output directory without mutation."""

    output_path = Path(output_dir)
    errors: list[str] = []
    result: dict[str, object] = {
        "command": "verify-local-flow",
        "valid": False,
        "output_dir": str(output_dir),
    }

    dispatch_path = output_path / "dispatch-message-log.json"
    flow_path = output_path / "flow-message-log.json"
    ledger_path = output_path / "ledger.json"
    receipts_path = output_path / "receipts.json"
    node_state_dir = output_path / "node-state"
    worker_log_dir = output_path / "worker-message-logs"

    for artifact_path in (dispatch_path, flow_path, ledger_path, receipts_path):
        if not artifact_path.exists():
            errors.append(f"missing required artifact: {artifact_path.name}")
    for directory_path in (node_state_dir, worker_log_dir):
        if not directory_path.exists():
            errors.append(f"missing required artifact directory: {directory_path.name}")
        elif not directory_path.is_dir():
            errors.append(f"required artifact path is not a directory: {directory_path.name}")

    dispatch_messages = _load_messages(dispatch_path, "dispatch-message-log.json", errors)
    flow_messages = _load_messages(flow_path, "flow-message-log.json", errors)
    dispatch_document = _load_json_object(dispatch_path, "dispatch-message-log.json", errors)
    flow_document = _load_json_object(flow_path, "flow-message-log.json", errors)

    ledger_summary: dict[str, Any] | None = None
    try:
        if ledger_path.exists():
            ledger, _extra_fields = load_existing_ledger_document(ledger_path)
            ledger_summary = ledger.summary_document(str(ledger_path))
    except LedgerPersistenceError as exc:
        errors.append(f"ledger.json: {exc}")

    receipt_document: dict[str, Any] | None = None
    try:
        if receipts_path.exists():
            receipt_document = load_receipt_document_if_exists(receipts_path)
    except ReceiptPersistenceError as exc:
        errors.append(f"receipts.json: {exc}")

    flow_metadata = _metadata(flow_document, "flow-message-log.json", errors)
    dispatch_metadata = _metadata(dispatch_document, "dispatch-message-log.json", errors)

    worker_paths_by_node = _worker_paths_from_metadata(flow_metadata, output_path, errors)
    if not worker_paths_by_node and worker_log_dir.is_dir():
        worker_paths_by_node = {
            _node_id_from_artifact_path(path): path for path in sorted(worker_log_dir.glob("*.json"))
        }

    worker_emitted_by_node: dict[str, list[Any]] = {}
    for node_id, worker_path in sorted(worker_paths_by_node.items()):
        _validate_inside_output_dir(worker_path, output_path, errors)
        if not worker_path.exists():
            errors.append(f"missing referenced worker message log: {worker_path}")
            continue
        try:
            emitted = load_worker_emitted_messages(worker_path)
        except MessageLogPersistenceError as exc:
            errors.append(f"{worker_path.name}: {exc}")
            continue
        unexpected = sorted(
            {message.message_type for message in emitted if message.message_type not in _EXPECTED_WORKER_MESSAGE_TYPES}
        )
        if unexpected:
            errors.append(
                f"{worker_path.name}: unsupported worker emitted message type(s): {', '.join(unexpected)}"
            )
        worker_emitted_by_node[node_id] = emitted

    node_states: dict[str, Any] = {}
    if node_state_dir.is_dir():
        node_ids = sorted(set(worker_paths_by_node) | {_node_id_from_artifact_path(path) for path in node_state_dir.glob("*.json")})
        for node_id in node_ids:
            state_path = node_state_dir / f"{_artifact_filename_for_node_id(node_id)}.json"
            if not state_path.exists():
                errors.append(f"missing node state for verified node: {node_id}")
                continue
            try:
                node_states[node_id] = load_node_processing_state(state_path, expected_node_id=node_id)
            except NodeStatePersistenceError as exc:
                errors.append(f"{state_path.name}: {exc}")

    _check_metadata_counts(
        flow_metadata=flow_metadata,
        dispatch_metadata=dispatch_metadata,
        dispatch_count=len(dispatch_messages),
        emitted_count=sum(len(messages) for messages in worker_emitted_by_node.values()),
        flow_count=len(flow_messages),
        errors=errors,
    )
    _check_referenced_artifact_paths(flow_metadata, output_path, errors)
    _check_flow_message_set(dispatch_messages, worker_emitted_by_node, flow_messages, errors)

    receipts = receipt_document.get("receipts", []) if isinstance(receipt_document, dict) else []
    if not isinstance(receipts, list):
        receipts = []
    _check_receipts(receipts, node_states, worker_emitted_by_node, errors)

    receipt_units = sum(
        receipt.get("credited_units", 0)
        for receipt in receipts
        if isinstance(receipt, dict) and isinstance(receipt.get("credited_units"), int)
    )
    total_units = int(ledger_summary["total_contribution_units"]) if ledger_summary is not None else 0
    if ledger_summary is not None:
        if total_units != receipt_units:
            errors.append(
                f"ledger total contribution units {total_units} does not match credited receipt total {receipt_units}"
            )
        metadata_units = flow_metadata.get("total_contribution_units") if flow_metadata is not None else None
        if isinstance(metadata_units, int) and total_units != metadata_units:
            errors.append(
                f"ledger total contribution units {total_units} does not match flow metadata total {metadata_units}"
            )

    sorted_errors = sorted(set(errors))
    if sorted_errors:
        result["errors"] = sorted_errors
        return result

    result.update(
        {
            "valid": True,
            "dispatch_message_count": len(dispatch_messages),
            "emitted_worker_message_count": sum(len(messages) for messages in worker_emitted_by_node.values()),
            "flow_message_count": len(flow_messages),
            "receipt_count": len(receipts),
            "processed_assignment_count": int(flow_metadata.get("processed_assignment_count", 0)),
            "skipped_processed_assignment_count": int(
                flow_metadata.get("skipped_processed_assignment_count", 0)
            ),
            "total_contribution_units": total_units,
            "verified_node_ids": sorted(node_states),
            "worker_message_log_paths": [str(worker_paths_by_node[node_id]) for node_id in sorted(worker_paths_by_node)],
            "errors": [],
        }
    )
    return result


def _load_messages(path: Path, label: str, errors: list[str]) -> list[Any]:
    if not path.exists():
        return []
    try:
        return load_message_log_messages(path)
    except MessageLogPersistenceError as exc:
        errors.append(f"{label}: {exc}")
        return []


def _load_json_object(path: Path, label: str, errors: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        errors.append(f"{label}: JSON is malformed: {exc.msg}")
        return None
    except OSError as exc:
        errors.append(f"{label}: could not read artifact: {exc}")
        return None
    if not isinstance(document, dict):
        errors.append(f"{label}: JSON must be an object")
        return None
    if document.get("version") != 1:
        errors.append(f"{label}: unsupported version {document.get('version')!r}; expected version 1")
    return document


def _metadata(document: dict[str, Any] | None, label: str, errors: list[str]) -> dict[str, Any]:
    if document is None:
        return {}
    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        errors.append(f"{label}: metadata must be an object")
        return {}
    return metadata


def _worker_paths_from_metadata(
    metadata: dict[str, Any], output_path: Path, errors: list[str]
) -> dict[str, Path]:
    raw_paths = metadata.get("worker_message_log_paths", {})
    if not isinstance(raw_paths, dict):
        errors.append("flow-message-log.json: metadata worker_message_log_paths must be an object")
        return {}
    paths: dict[str, Path] = {}
    for node_id, raw_path in raw_paths.items():
        if not isinstance(node_id, str) or node_id == "":
            errors.append("flow-message-log.json: worker_message_log_paths keys must be non-empty node ids")
            continue
        if not isinstance(raw_path, str) or raw_path == "":
            errors.append(f"flow-message-log.json: worker path for {node_id} must be a non-empty string")
            continue
        path = Path(raw_path)
        if not path.is_absolute() and not path.exists():
            path = output_path / raw_path
        paths[node_id] = path
    return paths


def _check_metadata_counts(
    *,
    flow_metadata: dict[str, Any],
    dispatch_metadata: dict[str, Any],
    dispatch_count: int,
    emitted_count: int,
    flow_count: int,
    errors: list[str],
) -> None:
    _check_int_field(flow_metadata, "message_count", flow_count, "flow-message-log.json", errors)
    _check_int_field(
        flow_metadata, "dispatch_message_count", dispatch_count, "flow-message-log.json", errors
    )
    _check_int_field(
        flow_metadata, "emitted_message_count", emitted_count, "flow-message-log.json", errors
    )
    _check_int_field(
        dispatch_metadata, "message_count", dispatch_count, "dispatch-message-log.json", errors
    )
    if flow_count != dispatch_count + emitted_count:
        errors.append(
            f"flow message count {flow_count} does not equal dispatch plus emitted count {dispatch_count + emitted_count}"
        )


def _check_int_field(
    metadata: dict[str, Any], field_name: str, actual: int, label: str, errors: list[str]
) -> None:
    expected = metadata.get(field_name)
    if not isinstance(expected, int) or isinstance(expected, bool):
        errors.append(f"{label}: metadata field '{field_name}' must be an integer")
    elif expected != actual:
        errors.append(f"{label}: metadata field '{field_name}' is {expected}, expected {actual}")


def _check_referenced_artifact_paths(
    metadata: dict[str, Any], output_path: Path, errors: list[str]
) -> None:
    for field_name in ("dispatch_message_log_path", "ledger_path"):
        raw_path = metadata.get(field_name)
        if not isinstance(raw_path, str) or raw_path == "":
            errors.append(f"flow-message-log.json: metadata field '{field_name}' must be a non-empty string")
            continue
        path = Path(raw_path)
        if not path.is_absolute() and not path.exists():
            path = output_path / raw_path
        _validate_inside_output_dir(path, output_path, errors)
        if not path.exists():
            errors.append(f"missing referenced artifact: {path}")


def _validate_inside_output_dir(path: Path, output_path: Path, errors: list[str]) -> None:
    try:
        path.resolve(strict=False).relative_to(output_path.resolve(strict=False))
    except ValueError:
        errors.append(f"referenced artifact is outside output_dir: {path}")


def _check_flow_message_set(
    dispatch_messages: list[Any],
    worker_emitted_by_node: dict[str, list[Any]],
    flow_messages: list[Any],
    errors: list[str],
) -> None:
    expected_ids = [message.message_id for message in dispatch_messages]
    for node_id in sorted(worker_emitted_by_node):
        expected_ids.extend(message.message_id for message in worker_emitted_by_node[node_id])
    actual_ids = [message.message_id for message in flow_messages]
    if actual_ids != expected_ids:
        errors.append("flow-message-log.json messages do not match dispatch messages plus worker emitted messages")


def _check_receipts(
    receipts: list[Any],
    node_states: dict[str, Any],
    worker_emitted_by_node: dict[str, list[Any]],
    errors: list[str],
) -> None:
    emitted_ids = {
        message.message_id
        for messages in worker_emitted_by_node.values()
        for message in messages
    }
    processed_ids_by_node = {
        node_id: set(state.processed_message_ids) for node_id, state in node_states.items()
    }
    receipt_ids_by_node: dict[str, set[str]] = {}
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, dict):
            continue
        node_id = receipt.get("node_id")
        assignment_id = receipt.get("assignment_message_id")
        if isinstance(node_id, str) and isinstance(assignment_id, str):
            receipt_ids_by_node.setdefault(node_id, set()).add(assignment_id)
            if assignment_id not in processed_ids_by_node.get(node_id, set()):
                errors.append(
                    f"receipt {index} assignment {assignment_id} is not recorded in node state for {node_id}"
                )
        for field_name in ("result_message_id", "contribution_message_id"):
            message_id = receipt.get(field_name)
            if isinstance(message_id, str) and message_id not in emitted_ids:
                errors.append(f"receipt {index} {field_name} {message_id} is missing from emitted worker messages")
    for node_id, receipt_ids in receipt_ids_by_node.items():
        missing = sorted(receipt_ids.difference(processed_ids_by_node.get(node_id, set())))
        if missing:
            errors.append(
                f"node state for {node_id} does not include receipt assignment id(s): {', '.join(missing)}"
            )


def _node_id_from_artifact_path(path: Path) -> str:
    return unquote(path.stem)


def _artifact_filename_for_node_id(node_id: str) -> str:
    from urllib.parse import quote

    return quote(node_id, safe="-._~")
