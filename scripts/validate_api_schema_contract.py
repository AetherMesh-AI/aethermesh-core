#!/usr/bin/env python3
"""Validate the versioned Phase 1 local API contract and write one receipt."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from aethermesh_core.api import create_app
from aethermesh_core.runtime import start_local_node_runtime
from aethermesh_core.runtime_service import NodeRuntimeService, RuntimeServiceError

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "phase-1-api-schema-contract.json"
EXAMPLES = ROOT / "examples" / "api-schema"


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def require_fields(value: dict[str, Any], fields: list[str], context: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ValueError(f"{context} is missing required fields: {', '.join(missing)}")


def validate_examples(contract: dict[str, Any]) -> list[str]:
    startup = load_object(EXAMPLES / "local-node-startup.json")
    submission = load_object(EXAMPLES / "local-job-submission.json")
    receipt = load_object(EXAMPLES / "local-validation-receipt-query.json")
    contribution = load_object(EXAMPLES / "local-contribution-lookup.json")
    operations = contract["operations"]
    require_fields(
        startup, operations["local_node_startup"]["request_required"], "startup example"
    )
    require_fields(
        startup["response"],
        operations["local_node_startup"]["response_required"],
        "startup response example",
    )
    require_fields(
        submission,
        operations["submit_local_job"]["request_required"],
        "submission example",
    )
    require_fields(
        receipt["response"],
        operations["local_validation_receipt"]["response_required"],
        "receipt response example",
    )
    require_fields(
        contribution["response"],
        operations["contribution_lookup"]["response_required"],
        "contribution response example",
    )
    require_fields(
        contribution["response"]["items"][0],
        operations["contribution_lookup"]["item_required"],
        "contribution item example",
    )
    return ["examples"]


def validate_runtime(contract: dict[str, Any]) -> list[str]:
    submission_example = load_object(EXAMPLES / "local-job-submission.json")
    operations = contract["operations"]
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        startup = start_local_node_runtime(root / "runtime").to_dict()
        require_fields(
            startup,
            operations["local_node_startup"]["response_required"],
            "runtime startup response",
        )
        service = NodeRuntimeService.from_home(root / "service")
        accepted = service.submit_local_job(submission_example)
        require_fields(
            accepted,
            operations["submit_local_job"]["response_required"],
            "submission response",
        )
        service.execute_submitted_local_job(accepted["job_id"], "worker-local-example")
        receipt = service.get_local_validation_receipt(work_id=accepted["job_id"])
        require_fields(
            receipt,
            operations["local_validation_receipt"]["response_required"],
            "validation receipt response",
        )
        contribution = service.contribution_summary()
        require_fields(
            contribution,
            operations["contribution_lookup"]["response_required"],
            "contribution lookup response",
        )
        require_fields(
            contribution["items"][0],
            operations["contribution_lookup"]["item_required"],
            "contribution item response",
        )
        try:
            service.submit_local_job(
                {
                    "job_type": "echo",
                    "payload": {},
                    "requested_validation_mode": "deterministic-local",
                }
            )
        except RuntimeServiceError:
            pass
        else:
            raise ValueError("submission accepted a missing creator_node_id")
    return ["runtime responses", "missing creator_node_id rejection"]


def validate_openapi(contract: dict[str, Any]) -> list[str]:
    documented = set(contract["route_inventory"])
    routes = {
        f"{method.upper()} {path}"
        for path, item in create_app().openapi()["paths"].items()
        for method in item
        if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}
    }
    missing = sorted(documented - routes)
    unexpected = sorted(routes - documented)
    if missing or unexpected:
        raise ValueError(
            f"OpenAPI route inventory drift: missing={missing}, unexpected={unexpected}"
        )
    return ["OpenAPI route inventory"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    contract = load_object(CONTRACT_PATH)
    if contract.get("contract_version") != "1.0.0":
        raise ValueError("unsupported API contract version")
    checks = (
        validate_examples(contract)
        + validate_runtime(contract)
        + validate_openapi(contract)
    )
    receipt = {
        "receipt_type": "phase_1_api_schema_validation",
        "contract_version": contract["contract_version"],
        "status": "passed",
        "checks": checks,
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
