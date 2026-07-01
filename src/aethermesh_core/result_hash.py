"""Canonical SHA-256 hashing for accounted local job results."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aethermesh_core.models import JobResult

RESULT_HASH_FIELDS = ("job_id", "node_id", "status", "output", "error")


def result_hash(result: JobResult) -> str:
    """Return the canonical lowercase SHA-256 digest for a ``JobResult``.

    The hash intentionally covers only the stable result identity/content fields
    that describe what a node reported and what was accounted. Contribution
    units, validation details, timestamps, message ids, receipt ids, and paths
    are intentionally excluded so the same result content has the same proof
    across local artifacts.
    """

    return result_hash_from_fields(
        job_id=result.job_id,
        node_id=result.node_id,
        status=result.status,
        output=result.output,
        error=result.error,
    )


def result_hash_from_fields(
    *,
    job_id: str,
    node_id: str,
    status: str,
    output: Any,
    error: str | None,
) -> str:
    """Hash the canonical result fields used by result messages and audits."""

    canonical = {
        "job_id": job_id,
        "node_id": node_id,
        "status": status,
        "output": output,
        "error": error,
    }
    encoded = _canonical_json_bytes(canonical)
    return hashlib.sha256(encoded).hexdigest()


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("result hash fields must be JSON-compatible") from exc
