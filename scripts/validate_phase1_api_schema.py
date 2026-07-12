#!/usr/bin/env python3
"""Validate the documented Phase 1 local API contract and examples."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from aethermesh_core.api import create_app
from aethermesh_core.runtime_service import NodeRuntimeService


class SchemaValidationError(ValueError):
    """Raised when a documented example does not satisfy its local schema."""


def _validate(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path} must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path} must be one of {schema['enum']!r}")
    expected_type = schema.get("type")
    type_checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
    }
    if expected_type and not type_checks[expected_type](value):
        raise SchemaValidationError(f"{path} must be a {expected_type}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        raise SchemaValidationError(f"{path} is shorter than minLength")
    if isinstance(value, int) and value < schema.get("minimum", value):
        raise SchemaValidationError(f"{path} is below minimum")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise SchemaValidationError(f"{path}.{key} is required")
        for key, nested_schema in schema.get("properties", {}).items():
            if key in value:
                _validate(value[key], nested_schema, f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _validate(item, schema["items"], f"{path}[{index}]")


def validate_contract(contract_path: Path) -> dict[str, Any]:
    raw_contract = contract_path.read_bytes()
    contract = json.loads(raw_contract)
    schemas = contract["schemas"]
    for example in contract["examples"]:
        _validate(example["payload"], schemas[example["schema"]])

    examples = {item["schema"]: item["payload"] for item in contract["examples"]}
    with tempfile.TemporaryDirectory() as temp_dir:
        service = NodeRuntimeService.from_home(Path(temp_dir))
        accepted = service.submit_local_job(examples["LocalJobSubmissionRequest"])
        _validate(accepted, schemas["LocalJobSubmissionAccepted"])
        _validate(
            service.get_local_job_status(accepted["job_id"]),
            schemas["LocalJobStatus"],
        )
        service.execute_submitted_local_job(accepted["job_id"], "worker-local-a")
        _validate(
            service.get_local_validation_receipt(work_id=accepted["job_id"]),
            schemas["LocalValidationReceipt"],
        )
        _validate(service.contribution_summary(), schemas["LocalContributionLookup"])

    documented_routes = set(contract["published_route_inventory"])
    published_routes = {
        f"{method.upper()} {path}"
        for path, methods in create_app().openapi()["paths"].items()
        for method in methods
    }
    if documented_routes != published_routes:
        missing = sorted(published_routes - documented_routes)
        stale = sorted(documented_routes - published_routes)
        raise SchemaValidationError(
            f"published route inventory mismatch; missing={missing}, stale={stale}"
        )
    for route in contract["route_contracts"]:
        if f"{route['method']} {route['path']}" not in published_routes:
            raise SchemaValidationError(
                f"contract route is not published: {route['method']} {route['path']}"
            )
        for field in ("request_schema", "response_schema"):
            if field in route and route[field] not in schemas:
                raise SchemaValidationError(f"unknown {field}: {route[field]}")
    return {
        "receipt_kind": "phase_1_local_api_schema_validation",
        "contract_version": contract["contract_version"],
        "example_count": len(contract["examples"]),
        "runtime_conformance_count": 4,
        "published_route_count": len(published_routes),
        "contract_sha256": hashlib.sha256(raw_contract).hexdigest(),
        "result": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/phase-1-local-api-schemas.json"),
    )
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt = validate_contract(args.contract)
    output = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
