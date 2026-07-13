"""Local validation gate for reported AetherMesh job results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from aethermesh_core.models import Job, JobResult
from aethermesh_core.runner import (
    build_basic_compute_output,
    build_hash_output,
    build_keyword_extract_output,
    build_schema_transform_output,
    build_text_chunk_output,
    build_text_embed_output,
    build_text_retrieve_output,
    build_text_stats_output,
)


@dataclass(frozen=True)
class ValidationResult:
    """Deterministic outcome from validating one reported job result."""

    job_id: str
    result_job_id: str
    valid: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the validation result into a JSON-compatible dictionary."""

        return asdict(self)


def validate_job_result(job: Job, result: JobResult) -> ValidationResult:
    """Validate a reported result against the assigned local job.

    Each supported work item declares output schema version 1 through its
    deterministic expected output. The schema gate runs before semantic value
    validation, so malformed, partial, or unexpected output is rejected with a
    stable schema path. This is fully local and deterministic.
    """

    if job.job_type not in {
        "echo",
        "hash",
        "basic_compute",
        "schema_transform",
        "keyword_extract",
        "text_chunk",
        "text_embed",
        "text_retrieve",
        "text_stats",
    }:
        return _invalid(job, result, "unsupported_job_type")
    if result.status != "completed":
        return _invalid(job, result, "result_not_completed")
    if result.job_id != job.job_id:
        return _invalid(job, result, "job_id_mismatch")
    if result.contribution_units != 1:
        return _invalid(job, result, "unexpected_contribution_units")

    expected_output: object
    if job.job_type == "echo":
        if "message" not in job.payload or not isinstance(job.payload["message"], str):
            return _invalid(job, result, "missing_payload_message")
        expected_output = job.payload["message"]
    elif job.job_type in {"hash", "basic_compute", "schema_transform"}:
        builders = {
            "hash": build_hash_output,
            "basic_compute": build_basic_compute_output,
            "schema_transform": build_schema_transform_output,
        }
        try:
            expected_output = builders[job.job_type](job.payload)
        except ValueError:
            return _invalid(job, result, f"malformed_{job.job_type}_payload")
    elif job.job_type == "text_stats":
        if "text" not in job.payload or not isinstance(job.payload["text"], str):
            return _invalid(job, result, "missing_payload_text")
        expected_output = build_text_stats_output(job.payload["text"])
    elif job.job_type == "keyword_extract":
        try:
            expected_output = build_keyword_extract_output(job.payload)
        except ValueError:
            return _invalid(job, result, "malformed_keyword_extract_payload")
    elif job.job_type == "text_chunk":
        try:
            expected_output = build_text_chunk_output(job.payload)
        except ValueError:
            return _invalid(job, result, "malformed_text_chunk_payload")
    elif job.job_type == "text_embed":
        try:
            expected_output = build_text_embed_output(job.payload)
        except ValueError:
            return _invalid(job, result, "malformed_text_embed_payload")
    else:  # text_retrieve is the remaining supported job type.
        try:
            expected_output = build_text_retrieve_output(job.payload)
        except ValueError:
            return _invalid(job, result, "malformed_text_retrieve_payload")

    if schema_error := _validate_declared_output_schema(
        job.job_type, expected_output, result.output
    ):
        return _invalid(job, result, schema_error)
    if result.output != expected_output:
        return _invalid(job, result, "output_mismatch")
    return ValidationResult(job.job_id, result.job_id, True, "ok")


def _validate_declared_output_schema(
    job_type: str, expected: object, actual: object, path: str = "output"
) -> str | None:
    """Validate the versioned output schema declared by one work item.

    Version 1 has no optional output fields: the deterministic local work item
    declares its complete output shape from its assigned payload. Semantic
    equality is checked separately to distinguish a correctly-shaped but wrong
    output from a schema failure.
    """

    schema_path = f"output_schema.v1.{job_type}.{path}"
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return f"{schema_path}: expected object"
        expected_fields = set(expected)
        actual_fields = set(actual)
        missing = sorted(expected_fields - actual_fields)
        if missing:
            return f"{schema_path}: missing required field {missing[0]}"
        unknown = sorted(actual_fields - expected_fields)
        if unknown:
            return f"{schema_path}: unknown field {unknown[0]}"
        for field in sorted(expected_fields):
            if reason := _validate_declared_output_schema(
                job_type, expected[field], actual[field], f"{path}.{field}"
            ):
                return reason
        return None
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return f"{schema_path}: expected array"
        if expected:
            for index, value in enumerate(actual):
                if reason := _validate_declared_output_schema(
                    job_type, expected[0], value, f"{path}[{index}]"
                ):
                    return reason
        return None
    if isinstance(expected, bool):
        valid = isinstance(actual, bool)
    elif isinstance(expected, int):
        valid = isinstance(actual, int) and not isinstance(actual, bool)
    elif isinstance(expected, float):
        valid = isinstance(actual, float)
    elif expected is None:
        valid = actual is None
    else:
        valid = isinstance(actual, type(expected))
    if not valid:
        return f"{schema_path}: expected {type(expected).__name__}"
    return None


def _invalid(job: Job, result: JobResult, reason: str) -> ValidationResult:
    return ValidationResult(
        job_id=job.job_id,
        result_job_id=result.job_id,
        valid=False,
        reason=reason,
    )
