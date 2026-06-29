"""Local validation gate for reported AetherMesh job results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from aethermesh_core.models import Job, JobResult


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

    The current prototype intentionally validates only the local ``echo``
    workload. Unsupported job types, failed results, mismatched job ids, missing
    echo messages, and mismatched outputs remain auditable but are invalid for
    contribution credit.
    """

    if job.job_type != "echo":
        return _invalid(job, result, "unsupported_job_type")
    if result.status != "completed":
        return _invalid(job, result, "result_not_completed")
    if result.job_id != job.job_id:
        return _invalid(job, result, "job_id_mismatch")
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


def _invalid(job: Job, result: JobResult, reason: str) -> ValidationResult:
    return ValidationResult(
        job_id=job.job_id,
        result_job_id=result.job_id,
        valid=False,
        reason=reason,
    )
