"""Deterministic local node registry for simulation roster state."""

from __future__ import annotations

from dataclasses import dataclass

from aethermesh_core.scheduler import NodeStatus, ScheduledNode


@dataclass
class _RegistryNode:
    node_id: str
    status: NodeStatus
    heartbeat_sequence: int = 0
    heartbeat_count: int = 0


class NodeRegistry:
    """In-memory source of truth for local simulation node state.

    The registry is intentionally dependency-free and deterministic. Heartbeats
    are local monotonic sequence values, not wall-clock timestamps or network
    liveness signals.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, _RegistryNode] = {}
        self._heartbeat_sequence = 0

    def register(
        self,
        node: str | ScheduledNode,
        status: NodeStatus = NodeStatus.AVAILABLE,
    ) -> ScheduledNode:
        """Register a node ID or ScheduledNode in deterministic insertion order."""

        scheduled_node = self._coerce_node(node, status)
        if scheduled_node.node_id in self._nodes:
            raise ValueError(f"duplicate node_id: {scheduled_node.node_id}")
        self._nodes[scheduled_node.node_id] = _RegistryNode(
            node_id=scheduled_node.node_id,
            status=scheduled_node.status,
        )
        return scheduled_node

    def mark_available(self, node_id: str) -> None:
        """Mark a known node available for future scheduler exports."""

        self._node_for_update(node_id).status = NodeStatus.AVAILABLE

    def mark_offline(self, node_id: str) -> None:
        """Mark a known node offline for future scheduler exports."""

        self._node_for_update(node_id).status = NodeStatus.OFFLINE

    def record_heartbeat(self, node_id: str) -> int:
        """Record one deterministic local heartbeat for a known node."""

        node = self._node_for_update(node_id)
        self._heartbeat_sequence += 1
        node.heartbeat_sequence = self._heartbeat_sequence
        node.heartbeat_count += 1
        return node.heartbeat_sequence

    def scheduled_nodes(self) -> list[ScheduledNode]:
        """Return scheduler-compatible nodes in registration order."""

        return [
            ScheduledNode(node_id=node.node_id, status=node.status)
            for node in self._nodes.values()
        ]

    def to_roster(self) -> list[dict[str, int | str]]:
        """Return JSON-compatible roster entries in registration order."""

        return [
            {
                "node_id": node.node_id,
                "status": node.status.value,
                "heartbeat_sequence": node.heartbeat_sequence,
                "heartbeat_count": node.heartbeat_count,
            }
            for node in self._nodes.values()
        ]

    def _node_for_update(self, node_id: str) -> _RegistryNode:
        self._validate_node_id(node_id)
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise KeyError(f"unknown node_id: {node_id}") from exc

    @classmethod
    def _coerce_node(
        cls, node: str | ScheduledNode, status: NodeStatus
    ) -> ScheduledNode:
        if isinstance(node, ScheduledNode):
            cls._validate_node_id(node.node_id)
            return node
        cls._validate_node_id(node)
        return ScheduledNode(node_id=node, status=status)

    @staticmethod
    def _validate_node_id(node_id: str) -> None:
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("node_id must be a non-empty string")
