"""Validate documented local API examples and route inventory."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

from aethermesh_core.api import create_app

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "local-api-schema-v1.json"


def _validate(value: object, schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    schema_type = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int}
    if schema_type in types and (
        not isinstance(value, types[schema_type]) or isinstance(value, bool)
    ):
        return [f"{label} must be a {schema_type}"]
    if isinstance(value, dict):
        for field in schema.get("required", []):
            if field not in value:
                errors.append(f"{label}.{field} is required")
        for field, child_schema in schema.get("properties", {}).items():
            if field in value:
                errors.extend(_validate(value[field], child_schema, f"{label}.{field}"))
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(_validate(item, schema["items"], f"{label}[{index}]"))
    return errors


def validate_contract() -> dict[str, object]:
    contract: dict[str, Any] = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    for name, example in contract["examples"].items():
        errors.extend(
            _validate(example["payload"], contract["schemas"][example["schema"]], name)
        )
    documented_routes = {tuple(key.split(" ", 1)) for key in contract["routes"]}
    implemented_routes = {
        (method.upper(), path)
        for path, operations in create_app().openapi()["paths"].items()
        for method in operations
        if method in {"get", "post", "put", "delete", "patch"}
    }
    if documented_routes != implemented_routes:
        errors.append("documented routes do not match generated OpenAPI routes")
    return {
        "contract_version": contract["contract_version"],
        "examples_checked": len(contract["examples"]),
        "routes_checked": len(documented_routes),
        "valid": not errors,
        "errors": errors,
    }


if __name__ == "__main__":
    receipt = validate_contract()
    rendered = json.dumps(receipt, sort_keys=True)
    if len(sys.argv) == 3 and sys.argv[1] == "--receipt":
        Path(sys.argv[2]).write_text(f"{rendered}\n", encoding="utf-8")
    elif len(sys.argv) != 1:
        raise SystemExit("usage: validate_local_api_schema.py [--receipt PATH]")
    print(rendered)
    raise SystemExit(0 if receipt["valid"] else 1)
