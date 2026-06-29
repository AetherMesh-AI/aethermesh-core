"""Contribution ledger helpers for local job results."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from aethermesh_core.models import JobResult


@dataclass(frozen=True)
class ContributionRecord:
    """Audit record derived from one local job result."""

    node_id: str
    job_id: str
    status: str
    contribution_units: int
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the record into a JSON-compatible dictionary."""

        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContributionRecord":
        """Deserialize one JSON-compatible contribution record."""

        _require_record_field(payload, "node_id", str)
        _require_record_field(payload, "job_id", str)
        _require_record_field(payload, "status", str)
        _require_record_field(payload, "contribution_units", int)
        message = payload.get("message")
        if message is not None and not isinstance(message, str):
            raise LedgerPersistenceError(
                "ledger record field 'message' must be a string or null"
            )
        return cls(
            node_id=payload["node_id"],
            job_id=payload["job_id"],
            status=payload["status"],
            contribution_units=payload["contribution_units"],
            message=message,
        )


@dataclass(frozen=True)
class ContributionSummary:
    """Aggregated contribution totals for one local node."""

    node_id: str
    completed_job_count: int
    failed_job_count: int
    total_result_count: int
    total_contribution_units: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize the summary into a JSON-compatible dictionary."""

        return asdict(self)


class ContributionLedger:
    """Small in-memory ledger for prototype contribution accounting."""

    def __init__(self, records: list[ContributionRecord] | None = None) -> None:
        self._records = list(records) if records is not None else []

    def record(self, result: JobResult) -> ContributionRecord:
        """Record one result and return its local contribution record.

        Only completed results with positive integer contribution units add to
        totals. Failed, zero, and negative-unit results are preserved for local
        auditability but contribute zero units.
        """

        units = _accounted_units(result)
        message = result.error if result.error is not None else _string_output(result.output)
        record = ContributionRecord(
            node_id=result.node_id,
            job_id=result.job_id,
            status=result.status,
            contribution_units=units,
            message=message,
        )
        self._records.append(record)
        return record

    def summary_for_node(self, node_id: str) -> ContributionSummary:
        """Return deterministic aggregate totals for one local node."""

        node_records = [record for record in self._records if record.node_id == node_id]
        return ContributionSummary(
            node_id=node_id,
            completed_job_count=sum(
                1 for record in node_records if record.status == "completed"
            ),
            failed_job_count=sum(1 for record in node_records if record.status == "failed"),
            total_result_count=len(node_records),
            total_contribution_units=sum(
                record.contribution_units for record in node_records
            ),
        )

    def node_ids(self) -> list[str]:
        """Return node ids present in the ledger in deterministic order."""

        return sorted({record.node_id for record in self._records})

    def summary_document(self, ledger_path: str | Path) -> dict[str, Any]:
        """Return a deterministic JSON-compatible summary of all records."""

        node_summaries = [self.summary_for_node(node_id) for node_id in self.node_ids()]
        return {
            "ledger_path": str(ledger_path),
            "record_count": len(self._records),
            "completed_result_count": sum(
                summary.completed_job_count for summary in node_summaries
            ),
            "failed_result_count": sum(
                summary.failed_job_count for summary in node_summaries
            ),
            "total_contribution_units": sum(
                summary.total_contribution_units for summary in node_summaries
            ),
            "nodes": [
                {
                    "node_id": summary.node_id,
                    "record_count": summary.total_result_count,
                    "completed_result_count": summary.completed_job_count,
                    "failed_result_count": summary.failed_job_count,
                    "total_contribution_units": summary.total_contribution_units,
                }
                for summary in node_summaries
            ],
        }

    def to_document(self, extra_fields: dict[str, Any] | None = None) -> dict[str, Any]:
        """Serialize the ledger into the small local JSON file shape."""

        document = dict(extra_fields) if extra_fields is not None else {}
        document["version"] = 1
        document["records"] = [record.to_dict() for record in self._records]
        return document

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> "ContributionLedger":
        """Deserialize a ledger from the local JSON file shape."""

        version = document.get("version")
        if version != 1:
            raise LedgerPersistenceError("ledger JSON must contain version 1")
        records = document.get("records")
        if not isinstance(records, list):
            raise LedgerPersistenceError("ledger JSON field 'records' must be a list")
        return cls([_record_from_json_value(record) for record in records])


class LedgerPersistenceError(ValueError):
    """Raised when a local ledger JSON file cannot be safely loaded or saved."""


def load_ledger_document(path: str | Path) -> tuple[ContributionLedger, dict[str, Any]]:
    """Load a JSON-backed local ledger, treating a missing file as empty.

    The returned metadata contains unknown top-level fields so callers can write
    them back without introducing a migration layer.
    """

    ledger_path = Path(path)
    if not ledger_path.exists():
        return ContributionLedger(), {}

    try:
        with ledger_path.open("r", encoding="utf-8") as handle:
            document = json.load(handle)
    except json.JSONDecodeError as exc:
        raise LedgerPersistenceError(f"ledger JSON is malformed: {exc.msg}") from exc
    except OSError as exc:
        raise LedgerPersistenceError(f"could not read ledger file: {exc}") from exc

    if not isinstance(document, dict):
        raise LedgerPersistenceError("ledger JSON must be an object")
    ledger = ContributionLedger.from_document(document)
    extras = {
        key: value for key, value in document.items() if key not in {"version", "records"}
    }
    return ledger, extras


def load_existing_ledger_document(
    path: str | Path,
) -> tuple[ContributionLedger, dict[str, Any]]:
    """Load an existing JSON-backed local ledger without creating defaults."""

    ledger_path = Path(path)
    if not ledger_path.exists():
        raise LedgerPersistenceError(f"ledger file does not exist: {ledger_path}")
    return load_ledger_document(ledger_path)


def save_ledger_document(
    path: str | Path,
    ledger: ContributionLedger,
    extra_fields: dict[str, Any] | None = None,
) -> None:
    """Write a JSON-backed local ledger via temp-file then atomic replace."""

    ledger_path = Path(path)
    parent = ledger_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    document = ledger.to_document(extra_fields)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=parent,
            prefix=f".{ledger_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, ledger_path)
    except OSError as exc:
        if temp_name is not None:
            _remove_temp_file(temp_name)
        raise LedgerPersistenceError(f"could not write ledger file: {exc}") from exc


def _accounted_units(result: JobResult) -> int:
    if result.status != "completed":
        return 0
    if not isinstance(result.contribution_units, int) or isinstance(
        result.contribution_units, bool
    ):
        raise ValueError("contribution_units must be an integer")
    return max(result.contribution_units, 0)


def _string_output(output: Any) -> str | None:
    if output is None:
        return None
    if isinstance(output, str):
        return output
    return str(output)


def _require_record_field(
    payload: dict[str, Any], field_name: str, expected_type: type
) -> None:
    value = payload.get(field_name)
    if not isinstance(value, expected_type) or isinstance(value, bool):
        raise LedgerPersistenceError(
            f"ledger record field '{field_name}' must be {expected_type.__name__}"
        )


def _record_from_json_value(value: Any) -> ContributionRecord:
    if not isinstance(value, dict):
        raise LedgerPersistenceError("ledger records must be objects")
    return ContributionRecord.from_dict(value)


def _remove_temp_file(path: str) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        return
