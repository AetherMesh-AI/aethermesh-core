"""Local in-memory runner for the first AetherMesh executable slice."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from aethermesh_core.models import Job, JobResult, NodeIdentity


class LocalRunner:
    """Execute supported local job types for a node."""

    SUPPORTED_ECHO_JOB_TYPE = "echo"
    SUPPORTED_TEXT_STATS_JOB_TYPE = "text_stats"
    SUPPORTED_KEYWORD_EXTRACT_JOB_TYPE = "keyword_extract"

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

        if job.job_type == self.SUPPORTED_KEYWORD_EXTRACT_JOB_TYPE:
            try:
                output = build_keyword_extract_output(job.payload)
            except ValueError as exc:
                return JobResult(
                    job_id=job.job_id,
                    node_id=self.identity.node_id,
                    status="failed",
                    output=None,
                    error=str(exc),
                    contribution_units=0,
                )
            return JobResult(
                job_id=job.job_id,
                node_id=self.identity.node_id,
                status="completed",
                output=output,
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


KEYWORD_EXTRACT_DEFAULT_LIMIT = 10
KEYWORD_EXTRACT_MAX_LIMIT = 50
KEYWORD_EXTRACT_STOPWORDS = frozenset(
    {"a", "an", "and", "are", "as", "for", "in", "is", "of", "on", "or", "the", "to", "with"}
)
_KEYWORD_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def build_keyword_extract_output(payload: dict[str, Any]) -> dict[str, object]:
    """Build deterministic keyword counts for a local ``keyword_extract`` job."""

    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("keyword_extract payload requires non-empty string field: text")

    limit = payload.get("limit", KEYWORD_EXTRACT_DEFAULT_LIMIT)
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
        or limit > KEYWORD_EXTRACT_MAX_LIMIT
    ):
        raise ValueError(
            "keyword_extract payload requires integer field: "
            f"limit between 1 and {KEYWORD_EXTRACT_MAX_LIMIT}"
        )

    tokens = [
        token
        for token in _KEYWORD_TOKEN_PATTERN.findall(text.lower())
        if token not in KEYWORD_EXTRACT_STOPWORDS
    ]
    counts = Counter(tokens)
    ordered_keywords = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    return {
        "keywords": [
            {"term": term, "count": count} for term, count in ordered_keywords[:limit]
        ],
        "unique_terms": len(counts),
        "total_terms": len(tokens),
    }
