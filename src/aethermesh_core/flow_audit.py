"""Read-only audit checks for completed local flow artifact directories."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from aethermesh_core.ledger import load_existing_ledger_document
from aethermesh_core.message_log import load_message_log_messages
from aethermesh_core.messages import MeshMessage
from aethermesh_core.receipts import _output_summary, load_receipt_document_if_exists
from aethermesh_core.result_hash import result_hash_from_fields


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
    dispatch_assignments_by_id = {
        message.message_id: message
        for message in dispatch_messages
        if message.message_type == "job_assigned"
    }

    expected_ledger_claims: Counter[tuple[Any, ...]] = Counter()
    for index, receipt in enumerate(receipts):
        context = _receipt_context(index, receipt)
        assignment_message_id = receipt["assignment_message_id"]
        assignment_message = dispatch_assignments_by_id.get(assignment_message_id)
        if assignment_message is None:
            raise FlowAuditError(
                f"{context} assignment_message_id not found in dispatch log: {assignment_message_id}"
            )
        _assert_assignment_matches_receipt(context, receipt, assignment_message.payload)

        result_message_id = receipt["result_message_id"]
        result_message = _find_flow_message_for_receipt(
            context,
            flow_messages,
            receipt,
            message_id=result_message_id,
            message_type="job_result_reported",
        )
        _assert_result_message_matches_receipt(context, receipt, result_message)

        contribution_message_id = receipt.get("contribution_message_id")
        if (
            not isinstance(contribution_message_id, str)
            or contribution_message_id == ""
        ):
            raise FlowAuditError(f"{context} contribution_message_id must be present")
        contribution_message = _find_flow_message_for_receipt(
            context,
            flow_messages,
            receipt,
            message_id=contribution_message_id,
            message_type="contribution_recorded",
        )
        _assert_contribution_message_matches_receipt(
            context, receipt, contribution_message
        )
        expected_ledger_claims[_ledger_claim_from_receipt(receipt)] += 1

    actual_ledger_claims = Counter(
        _ledger_claim_from_record(record) for record in ledger.to_document()["records"]
    )
    if expected_ledger_claims != actual_ledger_claims:
        missing = expected_ledger_claims - actual_ledger_claims
        extra = actual_ledger_claims - expected_ledger_claims
        detail = _ledger_mismatch_detail(missing, extra)
        raise FlowAuditError(
            f"receipt contribution claims do not match ledger records: {detail}"
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


def _receipt_context(index: int, receipt: dict[str, Any]) -> str:
    return (
        f"receipt entry {index} "
        f"job={receipt.get('job_id')} node={receipt.get('node_id')}"
    )


def _find_flow_message_for_receipt(
    context: str,
    flow_messages: list[MeshMessage],
    receipt: dict[str, Any],
    *,
    message_id: str,
    message_type: str,
) -> MeshMessage:
    """Find the flow message that matches one receipt.

    Worker logs use deterministic local message ids per node, so a merged flow
    log can contain the same emitted message id from multiple nodes. Match by id
    plus receipt identity instead of treating emitted ids as globally unique.
    """

    def matches_receipt_identity(message: MeshMessage) -> bool:
        if message.payload.get("job_id") != receipt["job_id"]:
            return False
        if message_type == "job_result_reported":
            return bool(message.sender_node_id == receipt["node_id"])
        if message_type == "contribution_recorded":
            return bool(message.payload.get("node_id") == receipt["node_id"])
        return False

    matches = [
        message
        for message in flow_messages
        if message.message_id == message_id
        and message.message_type == message_type
        and matches_receipt_identity(message)
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FlowAuditError(
            f"{context} {message_type} message_id not found in flow log: {message_id}"
        )
    raise FlowAuditError(
        f"{context} {message_type} message_id is ambiguous in flow log: {message_id}"
    )


def _assert_assignment_matches_receipt(
    context: str, receipt: dict[str, Any], payload: dict[str, Any]
) -> None:
    _assert_equal(
        context, "assignment.job_id", receipt["job_id"], payload.get("job_id")
    )
    _assert_equal(
        context, "assignment.job_type", receipt["job_type"], payload.get("job_type")
    )


def _assert_result_message_matches_receipt(
    context: str, receipt: dict[str, Any], message: MeshMessage
) -> None:
    if message.message_type != "job_result_reported":
        raise FlowAuditError(
            f"{context} result_message_id references {message.message_type}, expected job_result_reported"
        )
    _assert_equal(
        context, "result.job_id", receipt["job_id"], message.payload.get("job_id")
    )
    _assert_equal(context, "result.node_id", receipt["node_id"], message.sender_node_id)
    _assert_equal(
        context,
        "result.status",
        receipt["result_status"],
        message.payload.get("status"),
    )
    _assert_equal(
        context,
        "result.output_summary",
        receipt["output_summary"],
        _output_summary(message.payload.get("output")),
    )
    _assert_equal(
        context,
        "result.result_hash",
        receipt["result_hash"],
        message.payload.get("result_hash"),
    )
    recomputed_hash = result_hash_from_fields(
        job_id=message.payload["job_id"],
        node_id=message.sender_node_id,
        status=message.payload["status"],
        output=message.payload.get("output"),
        error=message.payload.get("error"),
    )
    _assert_equal(
        context,
        "result.recomputed_hash",
        message.payload.get("result_hash"),
        recomputed_hash,
    )


def _assert_contribution_message_matches_receipt(
    context: str, receipt: dict[str, Any], message: MeshMessage
) -> None:
    if message.message_type != "contribution_recorded":
        raise FlowAuditError(
            f"{context} contribution_message_id references {message.message_type}, expected contribution_recorded"
        )
    validation = receipt["validation"]
    _assert_equal(
        context, "contribution.job_id", receipt["job_id"], message.payload.get("job_id")
    )
    _assert_equal(
        context,
        "contribution.node_id",
        receipt["node_id"],
        message.payload.get("node_id"),
    )
    _assert_equal(
        context,
        "contribution.status",
        receipt["result_status"],
        message.payload.get("status"),
    )
    _assert_equal(
        context, "contribution.valid", validation["valid"], message.payload.get("valid")
    )
    _assert_equal(
        context,
        "contribution.validation",
        validation["reason"],
        message.payload.get("validation"),
    )
    _assert_equal(
        context,
        "contribution.contribution_units",
        receipt["credited_units"],
        message.payload.get("contribution_units"),
    )


def _ledger_claim_from_receipt(receipt: dict[str, Any]) -> tuple[Any, ...]:
    validation = receipt["validation"]
    return (
        receipt["node_id"],
        receipt["job_id"],
        receipt["result_status"],
        receipt["credited_units"],
        validation["valid"],
        validation["reason"],
        receipt["job_type"],
        receipt["result_hash"],
    )


def _ledger_claim_from_record(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record.get("node_id"),
        record.get("job_id"),
        record.get("status"),
        record.get("contribution_units"),
        record.get("validation_valid"),
        record.get("validation_reason"),
        record.get("job_type"),
        record.get("result_hash"),
    )


def _ledger_mismatch_detail(
    missing: Counter[tuple[Any, ...]], extra: Counter[tuple[Any, ...]]
) -> str:
    parts: list[str] = []
    if missing:
        parts.append(f"missing {_format_claim(next(iter(missing)))}")
    if extra:
        parts.append(f"extra {_format_claim(next(iter(extra)))}")
    return "; ".join(parts)


def _format_claim(claim: tuple[Any, ...]) -> str:
    if len(claim) == 7:
        node_id, job_id, status, units, valid, reason, job_type = claim
        result_hash = None
    else:
        node_id, job_id, status, units, valid, reason, job_type, result_hash = claim
    return (
        f"node={node_id} job={job_id} status={status} units={units} "
        f"valid={valid} reason={reason!r} job_type={job_type} result_hash={result_hash}"
    )


def _assert_equal(context: str, field_name: str, expected: Any, actual: Any) -> None:
    if actual != expected:
        raise FlowAuditError(
            f"{context} {field_name} mismatch: receipt={expected!r} artifact={actual!r}"
        )
