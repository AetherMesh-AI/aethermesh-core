"""Local validation gate for reported AetherMesh job results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from aethermesh_core.models import Job, JobResult
from aethermesh_core.runner import (
    build_extractive_summary_output,
    build_keyword_extract_output,
    build_text_chunk_output,
    build_text_embed_output,
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

    The current prototype intentionally validates only hardcoded local
    workloads. Unsupported job types, failed results, mismatched job ids,
    malformed payloads, and mismatched outputs remain auditable but are invalid
    for contribution credit.
    """

    if job.job_type not in {
        "echo",
        "extractive_summary",
        "keyword_extract",
        "text_chunk",
        "text_embed",
        "text_stats",
    }:
        return _invalid(job, result, "unsupported_job_type")
    if result.status != "completed":
        return _invalid(job, result, "result_not_completed")
    if result.job_id != job.job_id:
        return _invalid(job, result, "job_id_mismatch")
    if result.contribution_units != 1:
        return _invalid(job, result, "unexpected_contribution_units")

    if job.job_type == "echo":
        if "message" not in job.payload or not isinstance(job.payload["message"], str):
            return _invalid(job, result, "missing_payload_message")
        if result.output != job.payload["message"]:
            return _invalid(job, result, "output_mismatch")
        return ValidationResult(
            job_id=job.job_id,
            result_job_id=result.job_id,
            valid=True,
            reason="ok",
        )

    if job.job_type == "text_stats":
        if "text" not in job.payload or not isinstance(job.payload["text"], str):
            return _invalid(job, result, "missing_payload_text")
        if result.output != build_text_stats_output(job.payload["text"]):
            return _invalid(job, result, "output_mismatch")
        return ValidationResult(
            job_id=job.job_id,
            result_job_id=result.job_id,
            valid=True,
            reason="ok",
        )

    if job.job_type == "keyword_extract":
        try:
            expected_output = build_keyword_extract_output(job.payload)
        except ValueError:
            return _invalid(job, result, "malformed_keyword_extract_payload")
        if result.output != expected_output:
            return _invalid(job, result, "output_mismatch")
        return ValidationResult(
            job_id=job.job_id,
            result_job_id=result.job_id,
            valid=True,
            reason="ok",
        )

    if job.job_type == "text_chunk":
        try:
            expected_output = build_text_chunk_output(job.payload)
        except ValueError:
            return _invalid(job, result, "malformed_text_chunk_payload")
        if result.output != expected_output:
            return _invalid(job, result, "output_mismatch")
        return ValidationResult(
            job_id=job.job_id,
            result_job_id=result.job_id,
            valid=True,
            reason="ok",
        )

    if job.job_type == "text_embed":
        try:
            expected_output = build_text_embed_output(job.payload)
        except ValueError:
            return _invalid(job, result, "malformed_text_embed_payload")
        if result.output != expected_output:
            return _invalid(job, result, "output_mismatch")
        return ValidationResult(
            job_id=job.job_id,
            result_job_id=result.job_id,
            valid=True,
            reason="ok",
        )

    if job.job_type == "extractive_summary":
        try:
            expected_output = build_extractive_summary_output(job.payload)
        except ValueError:
            return _invalid(job, result, "malformed_extractive_summary_payload")
        if result.output != expected_output:
            return _invalid(job, result, "output_mismatch")
        return ValidationResult(
            job_id=job.job_id,
            result_job_id=result.job_id,
            valid=True,
            reason="ok",
        )

    return _invalid(
        job, result, "unsupported_job_type"
    )  # pragma: no cover  # justification: defensive fallback after supported job types are handled above


def _invalid(job: Job, result: JobResult, reason: str) -> ValidationResult:
    return ValidationResult(
        job_id=job.job_id,
        result_job_id=result.job_id,
        valid=False,
        reason=reason,
    )
