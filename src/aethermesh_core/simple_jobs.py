"""Strict local execution path for the first four deterministic job types."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

SIMPLE_JOB_TYPES = ("echo", "hash", "compute", "schema_transform")


class SimpleJobError(ValueError):
    """Raised when a Phase 1 simple-job request is malformed or unsupported."""


@dataclass(frozen=True)
class SimpleJobManifest:
    """Required, creator-attributed manifest for one bounded local job."""

    job_id: str
    job_type: str
    inputs: dict[str, Any]
    creator_node_id: str
    expected_output_shape: dict[str, Any]
    attribution_metadata: dict[str, Any]

    @property
    def reference(self) -> str:
        """Return the content-addressed manifest reference used in lineage."""

        return _sha256(asdict(self))


@dataclass(frozen=True)
class SimpleJobExecution:
    """Output, strict receipt, lineage, and validated contribution attribution."""

    output: Any
    validation_receipt: dict[str, Any]
    lineage: dict[str, str]
    contribution_attribution: dict[str, Any] | None


def parse_simple_job_manifest(document: object) -> SimpleJobManifest:
    """Validate a request manifest for one of the four bounded Phase 1 jobs."""

    if not isinstance(document, dict):
        raise SimpleJobError("simple job manifest must be an object")
    job_id = _required_string(document, "job_id")
    job_type = _required_string(document, "job_type")
    if job_type not in SIMPLE_JOB_TYPES:
        raise SimpleJobError(
            "unsupported simple job type: "
            f"{job_type}; allowed types: {', '.join(SIMPLE_JOB_TYPES)}"
        )
    creator_node_id = _required_string(document, "creator_node_id")
    inputs = _required_object(document, "inputs")
    expected_output_shape = _required_object(document, "expected_output_shape")
    attribution_metadata = _required_object(document, "attribution_metadata")
    if not attribution_metadata:
        raise SimpleJobError(
            "simple job manifest attribution_metadata must not be empty"
        )
    _require_json_value(inputs, "inputs")
    _require_json_value(expected_output_shape, "expected_output_shape")
    _require_json_value(attribution_metadata, "attribution_metadata")
    return SimpleJobManifest(
        job_id=job_id,
        job_type=job_type,
        inputs=inputs,
        creator_node_id=creator_node_id,
        expected_output_shape=expected_output_shape,
        attribution_metadata=attribution_metadata,
    )


def execute_simple_job(
    manifest: SimpleJobManifest,
    *,
    executor_node_id: str,
    timestamp: str | None = None,
) -> SimpleJobExecution:
    """Execute a manifest locally and issue a pass/fail validation receipt.

    Invalid declared output shapes receive no contribution attribution. Input
    errors are rejected before execution, so unsupported work is never routed.
    """

    if not executor_node_id.strip():
        raise SimpleJobError("executor_node_id must be a non-empty string")
    output = _execute(manifest.job_type, manifest.inputs)
    valid = _matches_shape(output, manifest.expected_output_shape)
    receipt_timestamp = timestamp or datetime.now(UTC).isoformat()
    if timestamp is not None:
        _parse_timestamp(timestamp)
    input_hash = _sha256(manifest.inputs)
    output_hash = _sha256(output)
    receipt = {
        "input_hash": input_hash,
        "output_hash": output_hash,
        "executor_node_id": executor_node_id,
        "timestamp": receipt_timestamp,
        "valid": valid,
        "status": "passed" if valid else "failed",
    }
    receipt_ref = _sha256(receipt)
    attempt_id = _sha256(
        {
            "manifest_ref": manifest.reference,
            "executor_node_id": executor_node_id,
            "receipt_ref": receipt_ref,
        }
    )
    lineage = {
        "manifest_ref": manifest.reference,
        "execution_attempt_id": attempt_id,
        "validation_receipt_ref": receipt_ref,
    }
    attribution = (
        {
            "creator_node_id": manifest.creator_node_id,
            "executor_node_id": executor_node_id,
            "job_id": manifest.job_id,
            "attribution_metadata": manifest.attribution_metadata,
        }
        if valid
        else None
    )
    return SimpleJobExecution(output, receipt, lineage, attribution)


def _execute(job_type: str, inputs: dict[str, Any]) -> Any:
    if job_type == "echo":
        payload = inputs.get("payload")
        if not isinstance(payload, str):
            raise SimpleJobError("echo inputs.payload must be a string")
        return payload
    if job_type == "hash":
        if "value" not in inputs:
            raise SimpleJobError("hash inputs.value is required")
        return {"sha256": _sha256(inputs["value"])}
    if job_type == "compute":
        operation = inputs.get("operation")
        operands = inputs.get("operands")
        if operation not in {"add", "multiply"}:
            raise SimpleJobError("compute inputs.operation must be add or multiply")
        if not isinstance(operands, list) or not operands:
            raise SimpleJobError("compute inputs.operands must be a non-empty list")
        if any(not _is_number(value) for value in operands):
            raise SimpleJobError("compute inputs.operands must contain only numbers")
        result = 0 if operation == "add" else 1
        for operand in operands:
            result = result + operand if operation == "add" else result * operand
        return {"result": result}
    if job_type == "schema_transform":
        value = inputs.get("value")
        schema = inputs.get("schema")
        if not isinstance(value, dict) or not isinstance(schema, dict) or not schema:
            raise SimpleJobError(
                "schema_transform inputs.value and inputs.schema must be non-empty objects"
            )
        if any(
            not isinstance(name, str) or not isinstance(kind, str)
            for name, kind in schema.items()
        ):
            raise SimpleJobError(
                "schema_transform inputs.schema must map field names to types"
            )
        output = {name: value.get(name) for name in sorted(schema)}
        if not _matches_shape(output, {"type": "object", "fields": schema}):
            raise SimpleJobError(
                "schema_transform input does not match declared schema"
            )
        return output
    raise SimpleJobError(f"unsupported simple job type: {job_type}")


def _matches_shape(value: Any, shape: dict[str, Any]) -> bool:
    value_type = shape.get("type")
    if value_type == "string":
        return isinstance(value, str)
    if value_type == "number":
        return _is_number(value)
    if value_type == "object":
        fields = shape.get("fields")
        if not isinstance(value, dict) or not isinstance(fields, dict):
            return False
        return set(value) == set(fields) and all(
            _matches_declared_type(value[name], kind) for name, kind in fields.items()
        )
    return False


def _matches_declared_type(value: Any, kind: object) -> bool:
    return (
        (kind == "string" and isinstance(value, str))
        or (
            kind == "integer" and isinstance(value, int) and not isinstance(value, bool)
        )
        or (kind == "number" and _is_number(value))
        or (kind == "boolean" and isinstance(value, bool))
    )


def _required_string(document: dict[str, Any], field: str) -> str:
    value = document.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SimpleJobError(f"simple job manifest {field} must be a non-empty string")
    return value


def _required_object(document: dict[str, Any], field: str) -> dict[str, Any]:
    value = document.get(field)
    if not isinstance(value, dict):
        raise SimpleJobError(f"simple job manifest {field} must be an object")
    return value


def _require_json_value(value: object, field: str) -> None:
    try:
        json.dumps(value, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise SimpleJobError(
            f"simple job manifest {field} must be JSON-compatible"
        ) from exc


def _sha256(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _parse_timestamp(timestamp: str) -> None:
    try:
        datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise SimpleJobError("timestamp must be ISO 8601") from exc
