"""Local in-memory runner for the first AetherMesh executable slice."""

from __future__ import annotations

from aethermesh_core.models import Job, JobResult, NodeIdentity


class LocalRunner:
    """Execute the single supported local job type for a node."""

    SUPPORTED_ECHO_JOB_TYPE = "echo"

    def __init__(self, identity: NodeIdentity) -> None:
        self.identity = identity

    def run(self, job: Job) -> JobResult:
        """Run one local job and return a structured result."""

        if job.job_type != self.SUPPORTED_ECHO_JOB_TYPE:
            return JobResult(
                job_id=job.job_id,
                node_id=self.identity.node_id,
                status="failed",
                output=None,
                error=f"Unsupported job type: {job.job_type}",
                contribution_units=0,
            )

        return JobResult(
            job_id=job.job_id,
            node_id=self.identity.node_id,
            status="completed",
            output=job.payload.get("message", ""),
            error=None,
            contribution_units=1,
        )
