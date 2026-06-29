"""In-memory contribution ledger for local job results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
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

    def __init__(self) -> None:
        self._records: list[ContributionRecord] = []

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
