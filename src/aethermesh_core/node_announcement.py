"""Local-only node heartbeat announcement helpers."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from aethermesh_core.message_log import MessageLogPersistenceError, write_message_log
from aethermesh_core.messages import MeshMessage
from aethermesh_core.scheduler import DEFAULT_LOCAL_CAPABILITIES, NodeStatus


class NodeAnnouncementError(ValueError):
    """Raised when a local node announcement cannot be built or written safely."""


def normalize_announcement_capabilities(
    capabilities: Iterable[str] | None,
) -> tuple[str, ...]:
    """Return deterministic, unique, non-empty node capabilities."""

    raw_capabilities = (
        DEFAULT_LOCAL_CAPABILITIES if capabilities is None else capabilities
    )
    normalized: set[str] = set()
    for index, capability in enumerate(raw_capabilities):
        if not isinstance(capability, str) or capability == "":
            raise NodeAnnouncementError(
                f"capability[{index}] must be a non-empty string"
            )
        normalized.add(capability)
    if not normalized:
        raise NodeAnnouncementError("capabilities must include at least one capability")
    return tuple(sorted(normalized))


def build_node_heartbeat_message(
    *,
    node_id: str,
    status: str = NodeStatus.AVAILABLE.value,
    capabilities: Iterable[str] | None = None,
) -> MeshMessage:
    """Build the single deterministic heartbeat message for a node announcement."""

    normalized_node_id = _validate_node_id(node_id)
    normalized_status = _validate_status(status)
    normalized_capabilities = normalize_announcement_capabilities(capabilities)
    return MeshMessage(
        message_id="msg-0001",
        message_type="node_heartbeat",
        sender_node_id=normalized_node_id,
        recipient_node_id=None,
        correlation_id=None,
        payload={
            "node_id": normalized_node_id,
            "status": normalized_status,
            "heartbeat_sequence": 1,
            "heartbeat_count": 1,
            "capabilities": list(normalized_capabilities),
        },
    )


def build_node_announcement_message_log_document(
    *,
    node_id: str,
    status: str = NodeStatus.AVAILABLE.value,
    capabilities: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build a version 1 message-log document for one announced local node."""

    message = build_node_heartbeat_message(
        node_id=node_id,
        status=status,
        capabilities=capabilities,
    )
    normalized_capabilities = list(message.payload["capabilities"])
    return {
        "version": 1,
        "metadata": {
            "source": "announce-local-node",
            "node_id": message.sender_node_id,
            "status": message.payload["status"],
            "message_count": 1,
            "capabilities": normalized_capabilities,
        },
        "messages": [message.to_dict()],
    }


def write_node_announcement_message_log(
    path: str | Path,
    document: dict[str, Any],
) -> None:
    """Write an announcement log while refusing to overwrite an existing path."""

    try:
        log_path = Path(path)
    except (TypeError, ValueError) as exc:
        raise NodeAnnouncementError(f"invalid message log path: {exc}") from exc
    if log_path.exists():
        raise NodeAnnouncementError(f"message log file already exists: {log_path}")
    try:
        write_message_log(log_path, document)
    except MessageLogPersistenceError as exc:
        raise NodeAnnouncementError(str(exc)) from exc


def announce_local_node(
    *,
    node_id: str,
    message_log_path: str | Path,
    status: str = NodeStatus.AVAILABLE.value,
    capabilities: Iterable[str] | None = None,
) -> dict[str, object]:
    """Build and write one local node heartbeat announcement message log."""

    document = build_node_announcement_message_log_document(
        node_id=node_id,
        status=status,
        capabilities=capabilities,
    )
    write_node_announcement_message_log(message_log_path, document)
    metadata = document["metadata"]
    return {
        "command": "announce-local-node",
        "node_id": metadata["node_id"],
        "status": metadata["status"],
        "capabilities": list(metadata["capabilities"]),
        "message_count": metadata["message_count"],
        "message_log_path": str(message_log_path),
    }


def _validate_node_id(node_id: object) -> str:
    if not isinstance(node_id, str) or not node_id.strip():
        raise NodeAnnouncementError("node_id must be a non-empty string")
    return node_id


def _validate_status(status: object) -> str:
    if not isinstance(status, str):
        raise NodeAnnouncementError("status must be a string")
    try:
        return NodeStatus(status).value
    except ValueError as exc:
        supported = ", ".join(status.value for status in NodeStatus)
        raise NodeAnnouncementError(f"status must be one of: {supported}") from exc
