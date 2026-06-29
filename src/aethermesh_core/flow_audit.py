"""Read-only audit checks for completed local flow artifact directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethermesh_core.ledger import load_existing_ledger_document
from aethermesh_core.message_log import load_message_log_messages
from aethermesh_core.receipts import load_receipt_document_if_exists


class FlowAuditError(ValueError):
    """Raised when local flow artifacts are missing or internally inconsistent."""


def audit_local_flow(output_dir: str | Path) -> dict[str, Any]:
    """Audit a completed ``run-local-flow`` artifact directory without writing files."""

    output_path = Path(output_dir)
    dispatch_message_log_path = output_path / "dispatch-message-log.json"
    flow_message_log_path = output_path / "flow-message-log.json"
    ledger_path = output_path / "ledger.json"
    receipts_path = output_path / "receipts.json"

    dispatch_messages = load_message_log_messages(dispatch_message_log_path)
    flow_messages = load_message_log_messages(flow_message_log_path)
    ledger, _extra_fields = load_existing_ledger_document(ledger_path)
    receipt_document = load_receipt_document_if_exists(receipts_path)
    if receipt_document is None:
        raise FlowAuditError(f"receipt file does not exist: {receipts_path}")

    receipts = receipt_document["receipts"]
    dispatch_assignment_ids = {
        message.message_id
        for message in dispatch_messages
        if message.message_type == "job_assigned"
    }
    flow_message_ids = {message.message_id for message in flow_messages}

    for index, receipt in enumerate(receipts):
        assignment_message_id = receipt["assignment_message_id"]
        if assignment_message_id not in dispatch_assignment_ids:
            raise FlowAuditError(
                f"receipt entry {index} assignment_message_id not found in dispatch log: {assignment_message_id}"
            )
        result_message_id = receipt["result_message_id"]
        if result_message_id not in flow_message_ids:
            raise FlowAuditError(
                f"receipt entry {index} result_message_id not found in flow log: {result_message_id}"
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

    ledger_summary = ledger.summary_document(ledger_path)
    ledger_total_units = int(ledger_summary["total_contribution_units"])
    credited_receipt_units = sum(int(receipt["credited_units"]) for receipt in receipts)
    if credited_receipt_units != ledger_total_units:
        raise FlowAuditError(
            "receipt credited units do not match ledger total contribution units: "
            f"receipts={credited_receipt_units} ledger={ledger_total_units}"
        )

    return {
        "ok": True,
        "output_dir": str(output_path),
        "artifacts": {
            "dispatch_message_log": str(dispatch_message_log_path),
            "flow_message_log": str(flow_message_log_path),
            "ledger": str(ledger_path),
            "receipts": str(receipts_path),
        },
        "counts": {
            "dispatch_messages": len(dispatch_messages),
            "flow_messages": len(flow_messages),
            "receipts": len(receipts),
            "ledger_records": int(ledger_summary["record_count"]),
            "total_contribution_units": ledger_total_units,
            "credited_receipt_units": credited_receipt_units,
        },
    }
