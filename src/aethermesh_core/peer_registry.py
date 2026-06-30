"""Read-only local peer roster derived from heartbeat messages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    load_message_log_messages,
)
from aethermesh_core.messages import MeshMessage


class PeerRegistryError(ValueError):
    """Raised when heartbeat-derived peer state cannot be summarized safely."""


@dataclass(frozen=True)
class PeerSummary:
    """Compact read-only view of one node's heartbeat-derived peer state."""

    node_id: str
    status: str
    heartbeat_count: int
    last_heartbeat_sequence: int
    capabilities: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "status": self.status,
            "heartbeat_count": self.heartbeat_count,
            "last_heartbeat_sequence": self.last_heartbeat_sequence,
            "capabilities": list(self.capabilities),
        }


def peer_summary_document(message_log_path: str | Path) -> dict[str, object]:
    """Load a version 1 message log and summarize node heartbeat peers.

    The source message log is read only. Only ``node_heartbeat`` messages affect
    the roster; every other valid message type is ignored.
    """

    try:
        messages = load_message_log_messages(message_log_path)
    except MessageLogPersistenceError as exc:
        raise PeerRegistryError(str(exc)) from exc

    peers: dict[str, PeerSummary] = {}
    for message in messages:
        if message.message_type != "node_heartbeat":
            continue
        heartbeat = _parse_heartbeat(message)
        current = peers.get(heartbeat.node_id)
        heartbeat_count = 1 if current is None else current.heartbeat_count + 1
        if (
            current is None
            or heartbeat.last_heartbeat_sequence > current.last_heartbeat_sequence
        ):
            peers[heartbeat.node_id] = PeerSummary(
                node_id=heartbeat.node_id,
                status=heartbeat.status,
                heartbeat_count=heartbeat_count,
                last_heartbeat_sequence=heartbeat.last_heartbeat_sequence,
                capabilities=heartbeat.capabilities,
            )
        else:
            peers[heartbeat.node_id] = PeerSummary(
                node_id=current.node_id,
                status=current.status,
                heartbeat_count=heartbeat_count,
                last_heartbeat_sequence=current.last_heartbeat_sequence,
                capabilities=list(current.capabilities),
            )

    return {
        "peers": [peers[node_id].to_dict() for node_id in sorted(peers)],
    }


def _parse_heartbeat(message: MeshMessage) -> PeerSummary:
    payload = message.payload
    node_id = payload.get("node_id")
    status = payload.get("status")
    heartbeat_sequence = payload.get("heartbeat_sequence")
    capabilities = payload.get("capabilities", [])

    if not isinstance(node_id, str) or node_id == "":
        raise PeerRegistryError(
            f"heartbeat message {message.message_id} payload field 'node_id' must be a non-empty string"
        )
    if not isinstance(status, str) or status == "":
        raise PeerRegistryError(
            f"heartbeat message {message.message_id} payload field 'status' must be a non-empty string"
        )
    if (
        not isinstance(heartbeat_sequence, int)
        or isinstance(heartbeat_sequence, bool)
        or heartbeat_sequence < 0
    ):
        raise PeerRegistryError(
            f"heartbeat message {message.message_id} payload field 'heartbeat_sequence' must be a non-negative integer"
        )
    if "heartbeat_count" in payload:
        heartbeat_count = payload["heartbeat_count"]
        if (
            not isinstance(heartbeat_count, int)
            or isinstance(heartbeat_count, bool)
            or heartbeat_count < 0
        ):
            raise PeerRegistryError(
                f"heartbeat message {message.message_id} payload field 'heartbeat_count' must be a non-negative integer"
            )
    parsed_capabilities = _parse_capabilities(capabilities, message.message_id)
    return PeerSummary(
        node_id=node_id,
        status=status,
        heartbeat_count=1,
        last_heartbeat_sequence=heartbeat_sequence,
        capabilities=parsed_capabilities,
    )


def _parse_capabilities(value: Any, message_id: str) -> list[str]:
    if not isinstance(value, list):
        raise PeerRegistryError(
            f"heartbeat message {message_id} payload field 'capabilities' must be a list of strings"
        )
    capabilities: list[str] = []
    for index, capability in enumerate(value):
        if not isinstance(capability, str) or capability == "":
            raise PeerRegistryError(
                f"heartbeat message {message_id} payload field 'capabilities[{index}]' must be a non-empty string"
            )
        capabilities.append(capability)
    return capabilities
