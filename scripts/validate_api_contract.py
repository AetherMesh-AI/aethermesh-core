#!/usr/bin/env python3
"""Validate the versioned Phase 1 local API contract and its examples."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from aethermesh_core.api import create_app

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "phase-1-local-api-contract.json"


def _matches_type(value: Any, declared: str) -> bool:
    base = declared.removeprefix("array[").removesuffix("]")
    if declared.startswith("array["):
        return isinstance(value, list) and all(
            _matches_type(item, base) for item in value
        )
    return {
        "string": lambda: isinstance(value, str),
        "object": lambda: isinstance(value, dict),
        "integer": lambda: isinstance(value, int) and not isinstance(value, bool),
    }[declared]()


def validate_payload(schema: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    errors = [
        f"missing required field {name}"
        for name in schema["required"]
        if name not in payload
    ]
    errors.extend(
        f"field {name} must be {declared}"
        for name, declared in schema["properties"].items()
        if name in payload and not _matches_type(payload[name], declared)
    )
    return errors


def validate_contract() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schemas = contract["schemas"]
    example_results: dict[str, str] = {}
    for name, example in contract["examples"].items():
        errors = validate_payload(schemas[example["schema"]], example["payload"])
        if errors:
            raise ValueError(f"example {name} is invalid: {', '.join(errors)}")
        example_results[name] = "passed"

    negative_cases = (
        ("job_submission", "creator_node_id"),
        ("job_submission_manifest", "manifest_type"),
        ("validation_receipt_lookup", "validation_status"),
        ("validation_receipt_lookup", "lineage_parent_ids"),
        ("validation_receipt_lookup", "contribution_attribution"),
    )
    negative_results: dict[str, str] = {}
    for example_name, field in negative_cases:
        example = contract["examples"][example_name]
        payload = copy.deepcopy(example["payload"])
        payload.pop(field)
        errors = validate_payload(schemas[example["schema"]], payload)
        if not errors:
            raise ValueError(f"missing {field} was incorrectly accepted")
        negative_results[f"{example_name}:{field}"] = "rejected"

    published_paths = set(create_app().openapi()["paths"])
    missing_routes = sorted(set(contract["required_route_paths"]) - published_paths)
    if missing_routes:
        raise ValueError(
            f"contract routes missing from generated OpenAPI: {missing_routes}"
        )
    return {
        "receipt_kind": "phase_1_api_contract_validation",
        "contract_version": contract["contract_version"],
        "examples": example_results,
        "missing_required_field_checks": negative_results,
        "openapi_route_match": "passed",
        "route_count": len(contract["required_route_paths"]),
        "result": "passed",
    }


if __name__ == "__main__":
    print(json.dumps(validate_contract(), indent=2, sort_keys=True))
