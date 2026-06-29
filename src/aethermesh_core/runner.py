"""Local in-memory runner for the first AetherMesh executable slice."""

from __future__ import annotations

from aethermesh_core.models import Job, JobResult, NodeIdentity


class LocalRunner:
    """Execute supported local job types for a node."""

    SUPPORTED_ECHO_JOB_TYPE = "echo"
    SUPPORTED_TEXT_STATS_JOB_TYPE = "text_stats"

    def __init__(self, identity: NodeIdentity) -> None:
        self.identity = identity

    def run(self, job: Job) -> JobResult:
        """Run one local job and return a structured result."""

        if job.job_type == self.SUPPORTED_ECHO_JOB_TYPE:
            return JobResult(
                job_id=job.job_id,
                node_id=self.identity.node_id,
                status="completed",
                output=job.payload.get("message", ""),
                error=None,
                contribution_units=1,
            )

        if job.job_type == self.SUPPORTED_TEXT_STATS_JOB_TYPE:
            text = job.payload.get("text")
            if not isinstance(text, str):
                return JobResult(
                    job_id=job.job_id,
                    node_id=self.identity.node_id,
                    status="failed",
                    output=None,
                    error="text_stats payload requires string field: text",
                    contribution_units=0,
                )
            return JobResult(
                job_id=job.job_id,
                node_id=self.identity.node_id,
                status="completed",
                output=build_text_stats_output(text),
                error=None,
                contribution_units=1,
            )

        return JobResult(
            job_id=job.job_id,
            node_id=self.identity.node_id,
            status="failed",
            output=None,
            error=f"Unsupported job type: {job.job_type}",
            contribution_units=0,
        )


def build_text_stats_output(text: str) -> dict[str, int | str]:
    """Build deterministic text statistics for a local ``text_stats`` job."""

    return {
        "character_count": len(text),
        "word_count": len(text.split()),
        "line_count": text.count("\n") + 1,
        "normalized_preview": " ".join(text.split())[:80],
    }
