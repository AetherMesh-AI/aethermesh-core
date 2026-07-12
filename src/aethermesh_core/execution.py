"""Executor boundary for resolved local work assignments.

This module deliberately has no scheduler or router dependency. Routing policy
creates :class:`PreparedWorkAssignment`; executors only validate, run, validate
outputs, and return immutable provenance-bearing receipts.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol

from aethermesh_core.models import Job, JobResult
from aethermesh_core.validation import ValidationResult, validate_job_result


class ExecutionAssignmentError(ValueError):
    """Raised before execution when a resolved assignment is malformed."""


class WorkRunner(Protocol):
    """Minimal execution dependency; intentionally independent of routing policy."""

    def run(self, job: Job) -> JobResult:
        """Run one already-assigned work item."""

        raise NotImplementedError


@dataclass(frozen=True)
class PreparedWorkAssignment:
    """Explicit handoff from scheduler/router policy to an executor.

    ``lineage`` and ``attribution`` are copied into immutable snapshots so the
    boundary does not share mutable policy state with the caller.
    """

    assignment_id: str
    work_item: Job
    executor_node_id: str
    manifest_ref: str
    creator_node_id: str | None
    lineage: Mapping[str, object]
    attribution: Mapping[str, object]

    def __post_init__(self) -> None:
        _require_non_empty_string(self.assignment_id, "assignment_id")
        _require_non_empty_string(self.executor_node_id, "executor_node_id")
        _require_non_empty_string(self.manifest_ref, "manifest_ref")
        if self.creator_node_id is not None:
            _require_non_empty_string(self.creator_node_id, "creator_node_id")
        if not isinstance(self.work_item, Job):
            raise ExecutionAssignmentError("work_item must be a Job")
        _require_non_empty_string(self.work_item.job_id, "work_item.job_id")
        _require_non_empty_string(self.work_item.job_type, "work_item.job_type")
        object.__setattr__(
            self,
            "work_item",
            Job(
                job_id=self.work_item.job_id,
                job_type=self.work_item.job_type,
                payload=deepcopy(self.work_item.payload),
            ),
        )
        object.__setattr__(self, "lineage", _snapshot_metadata(self.lineage, "lineage"))
        object.__setattr__(
            self, "attribution", _snapshot_metadata(self.attribution, "attribution")
        )


@dataclass(frozen=True)
class ExecutionReceipt:
    """Validation-gated, provenance-preserving outcome of one execution."""

    assignment_id: str
    manifest_ref: str
    creator_node_id: str | None
    executor_node_id: str
    job_id: str
    result: JobResult
    validation: ValidationResult
    lineage: Mapping[str, object]
    attribution: Mapping[str, object]

    @property
    def validation_status(self) -> str:
        """Return the stable validation state consumed by downstream accounting."""

        return "valid" if self.validation.valid else "invalid"

    def to_dict(self) -> dict[str, object]:
        """Serialize the receipt without exposing mutable metadata snapshots."""

        return {
            "assignment_id": self.assignment_id,
            "manifest_ref": self.manifest_ref,
            "creator_node_id": self.creator_node_id,
            "executor_node_id": self.executor_node_id,
            "job_id": self.job_id,
            "result": self.result.to_dict(),
            "validation": {
                "status": self.validation_status,
                "reason": self.validation.reason,
            },
            "lineage": deepcopy(dict(self.lineage)),
            "attribution": deepcopy(dict(self.attribution)),
        }


class LocalExecutor:
    """Run prepared local assignments without selecting or routing work."""

    def __init__(self, *, node_id: str, runner: WorkRunner) -> None:
        _require_non_empty_string(node_id, "node_id")
        self.node_id = node_id
        self.runner = runner

    def execute(self, assignment: PreparedWorkAssignment) -> ExecutionReceipt:
        """Run one prepared assignment and return its validation receipt."""

        if assignment.executor_node_id != self.node_id:
            raise ExecutionAssignmentError(
                "assignment executor_node_id does not match this executor node_id"
            )
        result = self.runner.run(assignment.work_item)
        validation = validate_job_result(assignment.work_item, result)
        if result.node_id != self.node_id:
            validation = ValidationResult(
                job_id=assignment.work_item.job_id,
                result_job_id=result.job_id,
                valid=False,
                reason="executor_node_id_mismatch",
            )
        return ExecutionReceipt(
            assignment_id=assignment.assignment_id,
            manifest_ref=assignment.manifest_ref,
            creator_node_id=assignment.creator_node_id,
            executor_node_id=self.node_id,
            job_id=assignment.work_item.job_id,
            result=result,
            validation=validation,
            lineage=assignment.lineage,
            attribution=assignment.attribution,
        )


def _require_non_empty_string(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExecutionAssignmentError(f"{field_name} must be a non-empty string")


def _snapshot_metadata(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ExecutionAssignmentError(f"{field_name} must be a mapping")
    if not all(isinstance(key, str) and key.strip() for key in value):
        raise ExecutionAssignmentError(f"{field_name} keys must be non-empty strings")
    return MappingProxyType(deepcopy(dict(value)))
