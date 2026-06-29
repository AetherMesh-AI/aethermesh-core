"""Local multi-node simulation for the AetherMesh prototype."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from aethermesh_core.ledger import ContributionLedger
from aethermesh_core.message_bus import LocalMessageBus
from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job, JobResult, NodeIdentity
from aethermesh_core.node_service import LocalNodeService
from aethermesh_core.node_registry import NodeRegistry
from aethermesh_core.runner import LocalRunner
from aethermesh_core.scheduler import JobAssignment, LocalScheduler, NodeStatus, ScheduledNode
from aethermesh_core.validation import ValidationResult


SimulationJobAssignment = JobAssignment


@dataclass(frozen=True)
class LocalSimulationResult:
    """Structured, deterministic output from a local multi-node simulation."""

    nodes: list[str]
    assignments: list[JobAssignment]
    results: list[JobResult]
    validations: list[ValidationResult]
    messages: list[MeshMessage]
    summaries: list[dict[str, Any]]
    node_roster: list[dict[str, int | str]]
    validation_summary: dict[str, int]
    totals: dict[str, int]
    accounted_results: list[JobResult]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the simulation result into a JSON-compatible dictionary.

        Validation-gated ``accounted_results`` are kept as structured data for
        callers that need to persist contribution accounting, but are omitted
        here to preserve the existing default simulation JSON shape.
        """

        return {
            "nodes": self.nodes,
            "assignments": [assignment.to_dict() for assignment in self.assignments],
            "results": [result.to_dict() for result in self.results],
            "validations": [validation.to_dict() for validation in self.validations],
            "messages": [message.to_dict() for message in self.messages],
            "summaries": self.summaries,
            "node_roster": self.node_roster,
            "validation_summary": self.validation_summary,
            "totals": self.totals,
        }


def run_local_simulation(
    node_ids: Sequence[str | ScheduledNode], jobs: list[Job]
) -> LocalSimulationResult:
    """Run local jobs across local node identities using scheduler assignment.

    This is intentionally local-only and in-memory: no networking, persistence,
    retries, async scheduling, or separate contribution accounting path.
    """

    if not node_ids:
        raise ValueError("node_ids must contain at least one node")

    registry = NodeRegistry()
    for node in node_ids:
        registered_node = registry.register(node)
        if registered_node.status == NodeStatus.AVAILABLE:
            registry.record_heartbeat(registered_node.node_id)
    nodes = registry.scheduled_nodes()
    ordered_node_ids = [node.node_id for node in nodes]
    ledger = ContributionLedger()
    message_bus = LocalMessageBus()
    for node_id in ordered_node_ids:
        message_bus.register_node(node_id)
    message_bus.register_node("local-scheduler")
    message_bus.register_node("local-ledger")
    services = {
        node.node_id: LocalNodeService(
            identity=NodeIdentity(node_id=node.node_id),
            message_bus=message_bus,
            runner=LocalRunner(NodeIdentity(node_id=node.node_id)),
            ledger=ledger,
        )
        for node in nodes
        if node.status == NodeStatus.AVAILABLE
    }
    scheduler = LocalScheduler(registry.scheduled_nodes())
    assignments = scheduler.assign_jobs(job.job_id for job in jobs)
    results: list[JobResult] = []
    accounted_results: list[JobResult] = []
    validations: list[ValidationResult] = []

    for job, assignment in zip(jobs, assignments):
        node_id = assignment.node_id
        assignment_message = _send_simulation_message(
            message_bus,
            message_type="job_assigned",
            sender_node_id="local-scheduler",
            recipient_node_id=node_id,
            payload={
                "job_id": job.job_id,
                "job_type": job.job_type,
                "payload": dict(job.payload),
                "node_id": node_id,
            },
            correlation_id=job.job_id,
        )
        inbox_result = services[node_id].process_inbox()
        processed = [
            processed_assignment
            for processed_assignment in inbox_result.processed
            if processed_assignment.message_id == assignment_message.message_id
        ]
        if len(processed) != 1:
            raise RuntimeError(
                f"expected one processed assignment for {assignment.job_id} on {node_id}"
            )
        processed_assignment = processed[0]
        results.append(processed_assignment.result)
        validations.append(processed_assignment.validation)
        accounted_results.append(
            replace(
                processed_assignment.result,
                contribution_units=processed_assignment.contribution_record.contribution_units,
            )
        )

    summaries = [
        _summary_to_simulation_dict(ledger, node_id) for node_id in ordered_node_ids
    ]
    node_roster = [
        _node_roster_entry(entry, assignments, summaries[index])
        for index, entry in enumerate(registry.to_roster())
    ]
    completed_jobs = sum(1 for result in results if result.status == "completed")
    failed_jobs = sum(1 for result in results if result.status == "failed")
    validation_summary = _validation_summary(validations)
    contribution_units = sum(int(summary["contribution_units"]) for summary in summaries)

    return LocalSimulationResult(
        nodes=ordered_node_ids,
        assignments=assignments,
        results=results,
        validations=validations,
        messages=message_bus.log(),
        summaries=summaries,
        node_roster=node_roster,
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
        accounted_results=accounted_results,
    )


def _node_roster_entry(
    roster_entry: dict[str, int | str],
    assignments: list[JobAssignment],
    summary: dict[str, Any],
) -> dict[str, int | str]:
    node_id = str(roster_entry["node_id"])
    return roster_entry | {
        "assigned_jobs": sum(1 for assignment in assignments if assignment.node_id == node_id),
        "contribution_units": int(summary["contribution_units"]),
    }


def _send_simulation_message(
    message_bus: LocalMessageBus,
    *,
    message_type: str,
    sender_node_id: str,
    recipient_node_id: str | None,
    payload: dict[str, Any],
    correlation_id: str | None,
) -> MeshMessage:
    message = MeshMessage(
        message_id=f"msg-{len(message_bus.log()) + 1:04d}",
        message_type=message_type,
        sender_node_id=sender_node_id,
        recipient_node_id=recipient_node_id,
        payload=payload,
        correlation_id=correlation_id,
    )
    return message_bus.send(message)


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
