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
    SUPPORTED_TEXT_CHUNK_JOB_TYPE = "text_chunk"

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

        if job.job_type == self.SUPPORTED_TEXT_CHUNK_JOB_TYPE:
            try:
                output = build_text_chunk_output(job.payload)
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


TEXT_CHUNK_DEFAULT_MAX_CHARS = 120
TEXT_CHUNK_MIN_MAX_CHARS = 1
TEXT_CHUNK_MAX_MAX_CHARS = 1000


def build_text_chunk_output(payload: dict[str, Any]) -> dict[str, object]:
    """Build stable character chunks for a local ``text_chunk`` job."""

    text = payload.get("text")
    if not isinstance(text, str):
        raise ValueError("text_chunk payload requires string field: text")

    max_chars = payload.get("max_chars", TEXT_CHUNK_DEFAULT_MAX_CHARS)
    if (
        not isinstance(max_chars, int)
        or isinstance(max_chars, bool)
        or max_chars < TEXT_CHUNK_MIN_MAX_CHARS
        or max_chars > TEXT_CHUNK_MAX_MAX_CHARS
    ):
        raise ValueError(
            "text_chunk payload requires integer field: "
            f"max_chars between {TEXT_CHUNK_MIN_MAX_CHARS} and {TEXT_CHUNK_MAX_MAX_CHARS}"
        )

    chunks: list[dict[str, int | str]] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        split_at = end if end == len(text) else _preferred_text_chunk_split(text, start, end)
        chunk_text = text[start:split_at]
        chunks.append(
            {
                "index": len(chunks),
                "text": chunk_text,
                "character_count": len(chunk_text),
            }
        )
        start = split_at

    return {
        "chunks": chunks,
        "chunk_count": len(chunks),
        "character_count": len(text),
    }


def _preferred_text_chunk_split(text: str, start: int, hard_end: int) -> int:
    """Return a deterministic split point no later than ``hard_end``."""

    if text[hard_end].isspace():
        return hard_end
    for index in range(hard_end - 1, start - 1, -1):
        if text[index].isspace():
            return index + 1
    return hard_end
