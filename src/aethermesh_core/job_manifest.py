"""Versioned JSON manifest loading for local batch simulation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aethermesh_core.models import Job
from aethermesh_core.scheduler import DEFAULT_LOCAL_CAPABILITIES, NodeStatus, ScheduledNode


class ManifestError(ValueError):
    """Raised when a local job manifest cannot be loaded or validated."""


@dataclass(frozen=True)
class LocalJobBatch:
    """Validated local batch inputs for the local simulation path."""

    nodes: list[ScheduledNode]
    jobs: list[Job]

    @property
    def node_ids(self) -> list[str]:
        """Return manifest node IDs in deterministic manifest order."""

        return [node.node_id for node in self.nodes]


def load_job_manifest(path: str | Path) -> LocalJobBatch:
    """Load and validate a version 1 local job-batch manifest."""

    manifest_path = Path(path)
    try:
        raw_manifest = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ManifestError(f"could not read manifest: {exc}") from exc

    try:
        document = json.loads(raw_manifest)
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest JSON is malformed: {exc.msg}") from exc

    if not isinstance(document, dict):
        raise ManifestError("manifest must be a JSON object")

    version = document.get("version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise ManifestError("manifest version must be integer 1")
    if version != 1:
        raise ManifestError(f"unsupported manifest version: {version}")

    return LocalJobBatch(
        nodes=_parse_nodes(document.get("nodes")),
        jobs=_parse_jobs(document.get("jobs")),
    )


def _parse_nodes(value: Any) -> list[ScheduledNode]:
    if not isinstance(value, list) or not value:
        raise ManifestError("manifest nodes must be a non-empty list")

    nodes: list[ScheduledNode] = []
    seen_node_ids: set[str] = set()
    for index, entry in enumerate(value):
        node = _parse_node_entry(entry, index)
        node_id = node.node_id
        if node_id in seen_node_ids:
            raise ManifestError(f"manifest contains duplicate node id: {node_id}")
        seen_node_ids.add(node_id)
        nodes.append(node)
    return nodes


def _parse_node_entry(entry: Any, index: int) -> ScheduledNode:
    if isinstance(entry, str):
        if not entry.strip():
            raise ManifestError(f"manifest nodes[{index}] must be a non-empty string")
        return ScheduledNode(node_id=entry, status=NodeStatus.AVAILABLE)

    if not isinstance(entry, dict):
        raise ManifestError(
            f"manifest nodes[{index}] must be a non-empty string or JSON object"
        )

    node_id = entry.get("node_id")
    if not isinstance(node_id, str) or not node_id.strip():
        raise ManifestError(f"manifest nodes[{index}].node_id must be a non-empty string")

    raw_status = entry.get("status", NodeStatus.AVAILABLE.value)
    if not isinstance(raw_status, str):
        raise ManifestError(f"manifest nodes[{index}].status must be a string")
    try:
        status = NodeStatus(raw_status)
    except ValueError as exc:
        supported_statuses = ", ".join(status.value for status in NodeStatus)
        raise ManifestError(
            f"manifest nodes[{index}].status must be one of: {supported_statuses}"
        ) from exc

    capabilities = _parse_capabilities(
        entry.get("capabilities", list(DEFAULT_LOCAL_CAPABILITIES)), index
    )
    return ScheduledNode(node_id=node_id, status=status, capabilities=capabilities)


def _parse_capabilities(value: Any, node_index: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ManifestError(
            f"manifest nodes[{node_index}].capabilities must be a non-empty list"
        )
    if not value:
        raise ManifestError(
            f"manifest nodes[{node_index}].capabilities must be a non-empty list"
        )

    capabilities: list[str] = []
    seen: set[str] = set()
    for capability_index, capability in enumerate(value):
        if not isinstance(capability, str) or not capability.strip():
            raise ManifestError(
                f"manifest nodes[{node_index}].capabilities[{capability_index}] must be a non-empty string"
            )
        if capability in seen:
            raise ManifestError(
                f"manifest nodes[{node_index}].capabilities contains duplicate capability: {capability}"
            )
        seen.add(capability)
        capabilities.append(capability)
    return tuple(capabilities)


def _parse_jobs(value: Any) -> list[Job]:
    if not isinstance(value, list) or not value:
        raise ManifestError("manifest jobs must be a non-empty list")

    return [_parse_job_entry(entry, index) for index, entry in enumerate(value)]


def _parse_job_entry(entry: Any, index: int) -> Job:
    if not isinstance(entry, dict):
        raise ManifestError(f"manifest jobs[{index}] must be a JSON object")

    job_id = entry.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ManifestError(f"manifest jobs[{index}].job_id must be a non-empty string")

    job_type = entry.get("job_type")
    if not isinstance(job_type, str) or not job_type.strip():
        raise ManifestError(f"manifest jobs[{index}].job_type must be a non-empty string")

    payload = entry.get("payload", {})
    if not isinstance(payload, dict):
        raise ManifestError(f"manifest jobs[{index}].payload must be a JSON object")

    return Job(job_id=job_id, job_type=job_type, payload=dict(payload))
