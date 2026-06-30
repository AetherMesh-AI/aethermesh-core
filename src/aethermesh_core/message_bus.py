"""Synchronous in-memory message bus for local AetherMesh simulation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from aethermesh_core.messages import MeshMessage


@dataclass(frozen=True)
class MessageDelivery:
    """A message accepted by the local bus with its deterministic sequence."""

    message: MeshMessage
    sequence: int


class LocalMessageBus:
    """Dependency-free local-only message bus for deterministic simulations."""

    def __init__(self) -> None:
        self._registered_node_ids: set[str] = set()
        self._log: list[MeshMessage] = []
        self._inboxes: dict[str, list[MeshMessage]] = {}

    def register_node(self, node_id: str) -> None:
        """Register a node or reserved local service actor with the bus."""

        if not isinstance(node_id, str) or node_id == "":
            raise ValueError("node_id must be a non-empty string")
        if node_id in self._registered_node_ids:
            raise ValueError(f"node_id is already registered: {node_id}")
        self._registered_node_ids.add(node_id)
        self._inboxes[node_id] = []

    def send(self, message: MeshMessage) -> MeshMessage:
        """Accept a message from a registered sender to a registered recipient."""

        if message.sender_node_id not in self._registered_node_ids:
            sender_id = message.sender_node_id
            raise ValueError(f"sender_node_id is not registered: {sender_id}")
        if (
            message.recipient_node_id is not None
            and message.recipient_node_id not in self._registered_node_ids
        ):
            recipient_id = message.recipient_node_id
            raise ValueError(f"recipient_node_id is not registered: {recipient_id}")

        self._log.append(message)
        if message.recipient_node_id is not None:
            self._inboxes[message.recipient_node_id].append(message)
        return message

    def log(self) -> list[MeshMessage]:
        """Return a copy of the ordered message log."""

        return list(self._log)

    def inbox_for(self, node_id: str) -> list[MeshMessage]:
        """Return a copy of the deterministic inbox for a registered node."""

        if node_id not in self._registered_node_ids:
            raise ValueError(f"node_id is not registered: {node_id}")
        return list(self._inboxes[node_id])


def send_numbered_message(
    message_bus: LocalMessageBus,
    *,
    message_type: str,
    sender_node_id: str,
    recipient_node_id: str | None,
    payload: Mapping[str, Any],
    correlation_id: str | None,
) -> MeshMessage:
    """Create and send a message with the next deterministic bus sequence id."""

    message = MeshMessage(
        message_id=f"msg-{len(message_bus.log()) + 1:04d}",
        message_type=message_type,
        sender_node_id=sender_node_id,
        recipient_node_id=recipient_node_id,
        payload=dict(payload),
        correlation_id=correlation_id,
    )
    return message_bus.send(message)
