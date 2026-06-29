"""Deterministic local scheduler for the AetherMesh prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable

from aethermesh_core.models import Job


DEFAULT_LOCAL_CAPABILITIES = ("echo", "text_stats")


class NoAvailableNodesError(ValueError):
    """Raised when local job assignment cannot find an available capable node."""


class NodeStatus(str, Enum):
    """Availability states needed by the local scheduler."""

    AVAILABLE = "available"
    OFFLINE = "offline"


@dataclass(frozen=True)
class ScheduledNode:
    """Local scheduler view of a node."""

    node_id: str
    status: NodeStatus = NodeStatus.AVAILABLE
    capabilities: tuple[str, ...] = DEFAULT_LOCAL_CAPABILITIES


@dataclass(frozen=True)
class JobAssignment:
    """Structured local assignment of one job to one node."""

    job_id: str
    node_id: str

    def to_dict(self) -> dict[str, str]:
        """Serialize the assignment into a JSON-compatible dictionary."""

        return asdict(self)


class LocalScheduler:
    """In-memory deterministic scheduler for local prototype jobs."""

    def __init__(self, nodes: Iterable[str | ScheduledNode]) -> None:
        self.nodes = tuple(_coerce_node(node) for node in nodes)

    def assign_jobs(self, jobs: Iterable[str | Job]) -> list[JobAssignment]:
        """Assign jobs round-robin across available capable nodes in input order."""

        job_list = list(jobs)
        if not job_list:
            return []

        available_nodes = [node for node in self.nodes if node.status == NodeStatus.AVAILABLE]
        assignments: list[JobAssignment] = []
        next_index_by_job_type: dict[str, int] = {}
        for job in job_list:
            job_id, job_type = _job_identity(job)
            eligible_nodes = [
                node for node in available_nodes if job_type in node.capabilities
            ]
            if not eligible_nodes:
                if not available_nodes:
                    raise NoAvailableNodesError(
                        f"no available nodes for job {job_id!r} of type {job_type!r}"
                    )
                raise NoAvailableNodesError(
                    f"no available node supports job {job_id!r} of type {job_type!r}"
                )
            next_index = next_index_by_job_type.get(job_type, 0)
            node = eligible_nodes[next_index % len(eligible_nodes)]
            next_index_by_job_type[job_type] = next_index + 1
            assignments.append(JobAssignment(job_id=job_id, node_id=node.node_id))

        return assignments


def _coerce_node(node: str | ScheduledNode) -> ScheduledNode:
    if isinstance(node, ScheduledNode):
        return node
    return ScheduledNode(node_id=node)


def _job_identity(job: str | Job) -> tuple[str, str]:
    if isinstance(job, Job):
        return job.job_id, job.job_type
    return job, DEFAULT_LOCAL_CAPABILITIES[0]
