"""Local in-memory runner for the first AetherMesh executable slice."""

from __future__ import annotations

import hashlib
import multiprocessing
import re
from collections import Counter
from queue import Empty
from typing import Any, cast

from aethermesh_core.models import Job, JobResult, NodeIdentity


class LocalRunner:
    """Execute supported local job types for a node."""

    SUPPORTED_ECHO_JOB_TYPE = "echo"
    SUPPORTED_TEXT_STATS_JOB_TYPE = "text_stats"
    SUPPORTED_KEYWORD_EXTRACT_JOB_TYPE = "keyword_extract"
    SUPPORTED_TEXT_CHUNK_JOB_TYPE = "text_chunk"
    SUPPORTED_TEXT_EMBED_JOB_TYPE = "text_embed"
    SUPPORTED_TEXT_RETRIEVE_JOB_TYPE = "text_retrieve"

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
            return self._run_payload_builder(job, build_keyword_extract_output)

        if job.job_type == self.SUPPORTED_TEXT_CHUNK_JOB_TYPE:
            return self._run_payload_builder(job, build_text_chunk_output)

        if job.job_type == self.SUPPORTED_TEXT_EMBED_JOB_TYPE:
            return self._run_payload_builder(job, build_text_embed_output)

        if job.job_type == self.SUPPORTED_TEXT_RETRIEVE_JOB_TYPE:
            return self._run_payload_builder(job, build_text_retrieve_output)

        return JobResult(
            job_id=job.job_id,
            node_id=self.identity.node_id,
            status="failed",
            output=None,
            error=f"Unsupported job type: {job.job_type}",
            contribution_units=0,
        )

    def _run_payload_builder(self, job: Job, builder: Any) -> JobResult:
        try:
            output = builder(job.payload)
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


def run_local_job(
    job: Job,
    identity: NodeIdentity,
    *,
    timeout_seconds: float | None = None,
    cancellation_requested: bool = False,
) -> JobResult:
    """Run local work with optional, local-only operator safety controls.

    Without metadata this uses the direct deterministic runner. A declared
    timeout isolates work in a process so expiry stops it; cancellation is
    checked before work starts.
    """

    if cancellation_requested:
        return _stopped_result(
            job, identity, "cancelled", "local cancellation requested"
        )
    if timeout_seconds is None:
        return LocalRunner(identity).run(job)

    context = multiprocessing.get_context("spawn")
    results = context.Queue()
    process = context.Process(
        target=_run_in_local_process, args=(job, identity, results)
    )
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        results.close()
        return _stopped_result(
            job,
            identity,
            "timed_out",
            f"local timeout after {timeout_seconds:g} seconds",
        )
    try:
        return cast(JobResult, results.get(timeout=1))
    except Empty:
        return JobResult(
            job_id=job.job_id,
            node_id=identity.node_id,
            status="failed",
            output=None,
            error="local runner exited without a result",
            contribution_units=0,
        )
    finally:
        results.close()


def _run_in_local_process(job: Job, identity: NodeIdentity, results: Any) -> None:
    results.put(LocalRunner(identity).run(job))


def _stopped_result(
    job: Job, identity: NodeIdentity, status: str, error: str
) -> JobResult:
    return JobResult(
        job_id=job.job_id,
        node_id=identity.node_id,
        status=status,
        output=None,
        error=error,
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
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "for",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
)
_KEYWORD_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
TEXT_EMBED_DEFAULT_DIMENSIONS = 8
TEXT_EMBED_MIN_DIMENSIONS = 2
TEXT_EMBED_MAX_DIMENSIONS = 64


def build_keyword_extract_output(payload: dict[str, Any]) -> dict[str, object]:
    """Build deterministic keyword counts for a local ``keyword_extract`` job."""

    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            "keyword_extract payload requires non-empty string field: text"
        )

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


def build_text_embed_output(payload: dict[str, Any]) -> dict[str, object]:
    """Build deterministic prototype feature counts for a local ``text_embed`` job."""

    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text_embed payload requires non-empty string field: text")

    dimensions = payload.get("dimensions", TEXT_EMBED_DEFAULT_DIMENSIONS)
    if (
        not isinstance(dimensions, int)
        or isinstance(dimensions, bool)
        or dimensions < TEXT_EMBED_MIN_DIMENSIONS
        or dimensions > TEXT_EMBED_MAX_DIMENSIONS
    ):
        raise ValueError(
            "text_embed payload requires integer field: "
            f"dimensions between {TEXT_EMBED_MIN_DIMENSIONS} and {TEXT_EMBED_MAX_DIMENSIONS}"
        )

    tokens = _KEYWORD_TOKEN_PATTERN.findall(text.lower())
    counts = Counter(tokens)
    vector = [0] * dimensions
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:8], "big") % dimensions
        vector[bucket] += 1

    return {
        "dimensions": dimensions,
        "token_count": len(tokens),
        "unique_terms": len(counts),
        "vector": vector,
    }


def build_text_retrieve_output(payload: dict[str, Any]) -> dict[str, object]:
    """Build deterministic token-overlap rankings for ``text_retrieve`` jobs."""

    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("text_retrieve payload requires non-empty string field: query")
    query_terms = sorted(set(_KEYWORD_TOKEN_PATTERN.findall(query.lower())))
    if not query_terms:
        raise ValueError(
            "text_retrieve payload requires query with at least one word token"
        )

    documents = payload.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError(
            "text_retrieve payload requires non-empty list field: documents"
        )

    limit = payload.get("limit", len(documents))
    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or limit < 1
        or limit > len(documents)
    ):
        raise ValueError(
            "text_retrieve payload requires integer field: "
            "limit between 1 and number of documents"
        )

    seen_document_ids: set[str] = set()
    matches: list[dict[str, Any]] = []
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            raise ValueError(f"text_retrieve documents[{index}] must be an object")
        document_id = document.get("id")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError(
                f"text_retrieve documents[{index}] requires non-empty string field: id"
            )
        if document_id in seen_document_ids:
            raise ValueError("text_retrieve document ids must be unique")
        seen_document_ids.add(document_id)

        text = document.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                f"text_retrieve documents[{index}] requires non-empty string field: text"
            )

        document_terms = set(_KEYWORD_TOKEN_PATTERN.findall(text.lower()))
        matched_terms = [term for term in query_terms if term in document_terms]
        matched_term_count = len(matched_terms)
        matches.append(
            {
                "id": document_id,
                "score": matched_term_count / len(query_terms),
                "matched_term_count": matched_term_count,
                "matched_terms": matched_terms,
            }
        )

    matches.sort(
        key=lambda match: (
            -float(match["score"]),
            -int(match["matched_term_count"]),
            str(match["id"]),
        )
    )
    return {"query_terms": query_terms, "matches": matches[:limit]}


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
        split_at = (
            end if end == len(text) else _preferred_text_chunk_split(text, start, end)
        )
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
