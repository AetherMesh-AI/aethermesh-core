"""Deterministic local scheduler for the AetherMesh prototype."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable


class NoAvailableNodesError(ValueError):
    """Raised when local job assignment has jobs but no available nodes."""


class NodeStatus(str, Enum):
    """Availability states needed by the local scheduler."""

    AVAILABLE = "available"
    OFFLINE = "offline"


@dataclass(frozen=True)
class ScheduledNode:
    """Local scheduler view of a node."""

    node_id: str
    status: NodeStatus = NodeStatus.AVAILABLE


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

    def assign_jobs(self, job_ids: Iterable[str]) -> list[JobAssignment]:
        """Assign job IDs round-robin across available nodes in input order."""

        job_id_list = list(job_ids)
        if not job_id_list:
            return []

        available_nodes = [
            node for node in self.nodes if node.status == NodeStatus.AVAILABLE
        ]
        if not available_nodes:
            raise NoAvailableNodesError("no available nodes for local job assignment")

        return [
            JobAssignment(
                job_id=job_id,
                node_id=available_nodes[index % len(available_nodes)].node_id,
            )
            for index, job_id in enumerate(job_id_list)
        ]


def _coerce_node(node: str | ScheduledNode) -> ScheduledNode:
    if isinstance(node, ScheduledNode):
        return node
    return ScheduledNode(node_id=node)
