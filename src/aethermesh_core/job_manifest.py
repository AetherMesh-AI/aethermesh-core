"""Versioned JSON manifest loading for local batch simulation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aethermesh_core.models import Job


class ManifestError(ValueError):
    """Raised when a local job manifest cannot be loaded or validated."""


@dataclass(frozen=True)
class LocalJobBatch:
    """Validated local batch inputs for the local simulation path."""

    node_ids: list[str]
    jobs: list[Job]


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
        node_ids=_parse_node_ids(document.get("nodes")),
        jobs=_parse_jobs(document.get("jobs")),
    )


def _parse_node_ids(value: Any) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ManifestError("manifest nodes must be a non-empty list")

    node_ids: list[str] = []
    seen_node_ids: set[str] = set()
    for index, node_id in enumerate(value):
        if not isinstance(node_id, str) or not node_id.strip():
            raise ManifestError(f"manifest nodes[{index}] must be a non-empty string")
        if node_id in seen_node_ids:
            raise ManifestError(f"manifest contains duplicate node id: {node_id}")
        seen_node_ids.add(node_id)
        node_ids.append(node_id)
    return node_ids


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
