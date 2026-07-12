#!/usr/bin/env python3
"""Validate the documented Phase 1 local API contract examples and routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aethermesh_core.api import create_app  # noqa: E402

EXAMPLES = {
    "local-node-registration-response.json": {
        "node_id",
        "creator_node_id",
        "manifest_path",
        "manifest_hash",
        "validation_receipt_path",
        "lineage_path",
        "validation_result",
        "network_mode",
    },
    "work-submission-request.json": {
        "schema_version",
        "job_type",
        "payload",
        "creator_node_id",
        "requested_validation_mode",
        "lineage_parent_refs",
        "attribution_metadata",
    },
    "validation-receipt-response.json": {
        "schema_version",
        "receipt_id",
        "work_id",
        "creator_node_id",
        "manifest_ref",
        "validation",
        "validator_identity",
        "lineage_parent_ids",
        "contribution_attribution",
        "evidence",
    },
    "contribution-lookup-response.json": {
        "network_mode",
        "summary_status",
        "accepted_work_count",
        "non_accepted_work_count",
        "items",
    },
}
ROUTES = {
    "/health",
    "/status",
    "/api/status",
    "/node",
    "/api/node",
    "/version",
    "/api/package",
    "/peers",
    "/api/peers",
    "/api/jobs",
    "/api/contributions",
    "/api/validation-receipts",
    "/api/audit-events",
    "/capabilities",
    "/api/capabilities",
    "/api/model-manifests",
    "/api/network",
    "/logs",
    "/api/logs",
    "/api/events",
    "/shutdown",
    "/restart",
}


def validate_examples() -> dict[str, str]:
    directory = ROOT / "examples" / "api-contract-v1"
    hashes: dict[str, str] = {}
    for filename, required in EXAMPLES.items():
        raw = (directory / filename).read_bytes()
        document: Any = json.loads(raw)
        if not isinstance(document, dict):
            raise ValueError(f"{filename} must contain a JSON object")
        missing = required - document.keys()
        if missing:
            raise ValueError(f"{filename} missing required fields: {sorted(missing)}")
        if document.get("schema_version", 1) != 1:
            raise ValueError(f"{filename} is not schema version 1")
        hashes[filename] = hashlib.sha256(raw).hexdigest()
    request = json.loads((directory / "work-submission-request.json").read_text())
    if (
        not isinstance(request["payload"], dict)
        or not isinstance(request["attribution_metadata"], dict)
        or not isinstance(request["lineage_parent_refs"], list)
    ):
        raise ValueError("work-submission-request.json has invalid provenance types")
    return hashes


def validate_routes() -> list[str]:
    published = set(create_app().openapi()["paths"])
    missing = sorted(ROUTES - published)
    if missing:
        raise ValueError(f"published OpenAPI is missing documented routes: {missing}")
    return sorted(ROUTES)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = {
        "schema_version": 1,
        "receipt_type": "phase_1_api_schema_validation",
        "validated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "examples": validate_examples(),
        "published_routes": validate_routes(),
        "result": "passed",
    }
    output = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
