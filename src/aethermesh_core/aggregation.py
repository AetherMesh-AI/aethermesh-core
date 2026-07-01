"""Deterministic local aggregation for completed flow artifact directories."""

from __future__ import annotations

import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from aethermesh_core.flow_audit import audit_local_flow
from aethermesh_core.receipts import load_receipt_document_if_exists

AGGREGATE_DOCUMENT_VERSION = 1


class AggregationError(ValueError):
    """Raised when a local flow aggregate cannot be built or written safely."""


def build_local_flow_aggregate(output_dir: str | Path) -> dict[str, Any]:
    """Build a deterministic aggregate document after auditing a flow directory."""

    audit_summary = audit_local_flow(output_dir)
    artifacts = audit_summary["artifacts"]
    receipts_path = artifacts["receipts"]
    receipt_document = load_receipt_document_if_exists(receipts_path)
    if receipt_document is None:
        raise AggregationError(f"receipt file does not exist: {receipts_path}")

    receipts = receipt_document["receipts"]
    accepted_results = [
        _accepted_result(receipt) for receipt in receipts if _is_accepted(receipt)
    ]
    accepted_results.sort(
        key=lambda entry: (
            str(entry["job_id"]),
            str(entry["job_type"]),
            str(entry["node_id"]),
            str(entry["assignment_message_id"]),
            str(entry["result_message_id"]),
        )
    )

    return {
        "version": AGGREGATE_DOCUMENT_VERSION,
        "output_dir": str(Path(output_dir)),
        "artifacts": {
            "dispatch_message_log": str(artifacts["dispatch_message_log"]),
            "flow_message_log": str(artifacts["flow_message_log"]),
            "ledger": str(artifacts["ledger"]),
            "receipts": str(artifacts["receipts"]),
        },
        "counts": {
            "receipts": len(receipts),
            "accepted_results": len(accepted_results),
            "invalid_or_zero_credit_receipts": len(receipts) - len(accepted_results),
            "total_credited_units": sum(
                int(entry["credited_units"]) for entry in accepted_results
            ),
        },
        "totals_by_job_type": _totals_by_field(accepted_results, "job_type"),
        "totals_by_node_id": _totals_by_field(accepted_results, "node_id"),
        "validation_totals": _validation_totals(receipts),
        "accepted_results": accepted_results,
        "audit_summary": audit_summary,
    }


def aggregate_local_flow(
    output_dir: str | Path, aggregate_path: str | Path | None = None
) -> dict[str, Any]:
    """Audit, build, and persist a local flow aggregate, returning a CLI summary."""

    aggregate_document = build_local_flow_aggregate(output_dir)
    aggregate_output_path = (
        Path(aggregate_path)
        if aggregate_path is not None
        else Path(output_dir) / "aggregate-result.json"
    )
    write_aggregate_document(aggregate_output_path, aggregate_document)
    return {
        "command": "aggregate-local-flow",
        "output_dir": str(Path(output_dir)),
        "aggregate_path": str(aggregate_output_path),
        "counts": aggregate_document["counts"],
        "totals_by_job_type": aggregate_document["totals_by_job_type"],
        "totals_by_node_id": aggregate_document["totals_by_node_id"],
        "audit_summary": aggregate_document["audit_summary"],
    }


def write_aggregate_document(path: str | Path, document: dict[str, Any]) -> None:
    """Write an aggregate document via temp-file then atomic replace."""

    _validate_aggregate_document(document)
    aggregate_path = Path(path)
    parent = aggregate_path.parent
    temp_name: str | None = None
    try:
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=parent,
            prefix=f".{aggregate_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, aggregate_path)
    except (OSError, TypeError, ValueError) as exc:
        if temp_name is not None:
            _remove_temp_file(temp_name)
        raise AggregationError(f"could not write aggregate file: {exc}") from exc


def _accepted_result(receipt: dict[str, Any]) -> dict[str, Any]:
    validation = receipt["validation"]
    return {
        "job_id": receipt["job_id"],
        "job_type": receipt["job_type"],
        "node_id": receipt["node_id"],
        "result_status": receipt["result_status"],
        "credited_units": int(receipt["credited_units"]),
        "validation_valid": bool(validation["valid"]),
        "validation_reason": validation["reason"],
        "output_summary": receipt["output_summary"],
        "assignment_message_id": receipt["assignment_message_id"],
        "result_message_id": receipt["result_message_id"],
        "contribution_message_id": receipt["contribution_message_id"],
    }


def _is_accepted(receipt: dict[str, Any]) -> bool:
    validation = receipt["validation"]
    return bool(validation["valid"]) and int(receipt["credited_units"]) > 0


def _totals_by_field(
    accepted_results: list[dict[str, Any]], field_name: str
) -> dict[str, int]:
    totals: Counter[str] = Counter()
    for entry in accepted_results:
        totals[str(entry[field_name])] += int(entry["credited_units"])
    return dict(sorted(totals.items()))


def _validation_totals(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: Counter[str] = Counter()
    valid = 0
    invalid = 0
    zero_credit = 0
    failed_status = 0
    for receipt in receipts:
        validation = receipt["validation"]
        if validation["valid"]:
            valid += 1
        else:
            invalid += 1
        if int(receipt["credited_units"]) == 0:
            zero_credit += 1
        if receipt["result_status"] != "completed":
            failed_status += 1
        reasons[str(validation["reason"])] += 1
    return {
        "valid": valid,
        "invalid": invalid,
        "zero_credit": zero_credit,
        "failed_status": failed_status,
        "reasons": dict(sorted(reasons.items())),
    }


def _validate_aggregate_document(document: dict[str, Any]) -> None:
    version = document.get("version")
    if version != AGGREGATE_DOCUMENT_VERSION or isinstance(version, bool):
        raise AggregationError("aggregate JSON must contain version 1")
    if not isinstance(document.get("accepted_results"), list):
        raise AggregationError("aggregate JSON field 'accepted_results' must be a list")
    if not isinstance(document.get("counts"), dict):
        raise AggregationError("aggregate JSON field 'counts' must be an object")


def _remove_temp_file(path: str) -> None:
    Path(path).unlink(missing_ok=True)
