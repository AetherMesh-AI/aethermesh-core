"""Local multi-node simulation for the AetherMesh prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any

from aethermesh_core.ledger import ContributionLedger
from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job, JobResult, NodeIdentity
from aethermesh_core.runner import LocalRunner
from aethermesh_core.validation import ValidationResult, validate_job_result


@dataclass(frozen=True)
class SimulationJobAssignment:
    """Deterministic local assignment of one job to one node."""

    job_id: str
    node_id: str

    def to_dict(self) -> dict[str, str]:
        """Serialize the assignment into a JSON-compatible dictionary."""

        return asdict(self)


@dataclass(frozen=True)
class LocalSimulationResult:
    """Structured, deterministic output from a local multi-node simulation."""

    nodes: list[str]
    assignments: list[SimulationJobAssignment]
    results: list[JobResult]
    validations: list[ValidationResult]
    messages: list[MeshMessage]
    summaries: list[dict[str, Any]]
    validation_summary: dict[str, int]
    totals: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the simulation result into a JSON-compatible dictionary."""

        return {
            "nodes": self.nodes,
            "assignments": [assignment.to_dict() for assignment in self.assignments],
            "results": [result.to_dict() for result in self.results],
            "validations": [validation.to_dict() for validation in self.validations],
            "messages": [message.to_dict() for message in self.messages],
            "summaries": self.summaries,
            "validation_summary": self.validation_summary,
            "totals": self.totals,
        }


def run_local_simulation(node_ids: list[str], jobs: list[Job]) -> LocalSimulationResult:
    """Run local jobs across local node identities using round-robin assignment.

    This is intentionally local-only and in-memory: no networking, persistence,
    retries, async scheduling, or separate contribution accounting path.
    """

    if not node_ids:
        raise ValueError("node_ids must contain at least one node")

    ledger = ContributionLedger()
    runners = {
        node_id: LocalRunner(NodeIdentity(node_id=node_id)) for node_id in node_ids
    }
    assignments: list[SimulationJobAssignment] = []
    results: list[JobResult] = []
    validations: list[ValidationResult] = []
    messages: list[MeshMessage] = []

    for index, job in enumerate(jobs):
        node_id = node_ids[index % len(node_ids)]
        assignment = SimulationJobAssignment(job_id=job.job_id, node_id=node_id)
        messages.append(
            _simulation_message(
                messages,
                message_type="job_assigned",
                sender_node_id="local-scheduler",
                recipient_node_id=node_id,
                payload={
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "node_id": node_id,
                },
                correlation_id=job.job_id,
            )
        )
        result = runners[node_id].run(job)
        messages.append(
            _simulation_message(
                messages,
                message_type="job_result_reported",
                sender_node_id=node_id,
                recipient_node_id="local-ledger",
                payload={
                    "job_id": result.job_id,
                    "status": result.status,
                    "success": result.status == "completed",
                    "output": result.output,
                    "error": result.error,
                },
                correlation_id=job.job_id,
            )
        )

        assignments.append(assignment)
        results.append(result)
        validation = validate_job_result(job, result)
        validations.append(validation)
        record_result = result if validation.valid else replace(result, contribution_units=0)
        record = ledger.record(record_result)
        messages.append(
            _simulation_message(
                messages,
                message_type="contribution_recorded",
                sender_node_id="local-ledger",
                recipient_node_id=node_id,
                payload={
                    "job_id": record.job_id,
                    "node_id": record.node_id,
                    "status": record.status,
                    "validation": validation.reason,
                    "valid": validation.valid,
                    "contribution_units": record.contribution_units,
                },
                correlation_id=job.job_id,
            )
        )

    summaries = [_summary_to_simulation_dict(ledger, node_id) for node_id in node_ids]
    completed_jobs = sum(1 for result in results if result.status == "completed")
    failed_jobs = sum(1 for result in results if result.status == "failed")
    validation_summary = _validation_summary(validations)
    contribution_units = sum(int(summary["contribution_units"]) for summary in summaries)

    return LocalSimulationResult(
        nodes=list(node_ids),
        assignments=assignments,
        results=results,
        validations=validations,
        messages=messages,
        summaries=summaries,
        validation_summary=validation_summary,
        totals={
            "nodes": len(node_ids),
            "jobs": len(jobs),
            "results": len(results),
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "valid_results": validation_summary["valid"],
            "invalid_results": validation_summary["invalid"],
            "unsupported_results": validation_summary["unsupported"],
            "contribution_units": contribution_units,
        },
    )


def _simulation_message(
    existing_messages: list[MeshMessage],
    *,
    message_type: str,
    sender_node_id: str,
    recipient_node_id: str | None,
    payload: dict[str, Any],
    correlation_id: str | None,
) -> MeshMessage:
    return MeshMessage(
        message_id=f"msg-{len(existing_messages) + 1:04d}",
        message_type=message_type,
        sender_node_id=sender_node_id,
        recipient_node_id=recipient_node_id,
        payload=payload,
        correlation_id=correlation_id,
    )


def _summary_to_simulation_dict(
    ledger: ContributionLedger, node_id: str
) -> dict[str, int | str]:
    summary = ledger.summary_for_node(node_id)
    return {
        "node_id": summary.node_id,
        "completed_jobs": summary.completed_job_count,
        "failed_jobs": summary.failed_job_count,
        "results": summary.total_result_count,
        "contribution_units": summary.total_contribution_units,
    }


def _validation_summary(validations: list[ValidationResult]) -> dict[str, int]:
    invalid = sum(1 for validation in validations if not validation.valid)
    unsupported = sum(
        1 for validation in validations if validation.reason == "unsupported_job_type"
    )
    return {
        "valid": sum(1 for validation in validations if validation.valid),
        "invalid": invalid,
        "unsupported": unsupported,
    }
