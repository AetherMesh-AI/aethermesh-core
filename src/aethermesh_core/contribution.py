"""Deterministic contribution scoring for validated local workload results."""

from __future__ import annotations

from math import ceil
from typing import Any, cast

from aethermesh_core.models import Job, JobResult

ECHO_CONTRIBUTION_UNITS = 1

TEXT_STATS_CHARACTER_BUCKET = 100
TEXT_STATS_MAX_UNITS = 5

KEYWORD_EXTRACT_KEYWORDS_PER_UNIT = 5
KEYWORD_EXTRACT_MAX_UNITS = 5

TEXT_CHUNK_CHUNKS_PER_UNIT = 2
TEXT_CHUNK_MAX_UNITS = 5

TEXT_EMBED_TOKENS_PER_UNIT = 10
TEXT_EMBED_DIMENSIONS_PER_UNIT = 16
TEXT_EMBED_MAX_UNITS = 6

EXTRACTIVE_SUMMARY_SENTENCES_PER_UNIT = 2
EXTRACTIVE_SUMMARY_MAX_UNITS = 5


def score_validated_contribution(job: Job, result: JobResult) -> int:
    """Return capped integer contribution units for one validated local result.

    This scorer is intentionally local-only and deterministic. Callers must run
    validation first and must use zero units for invalid results; this function
    still returns zero for malformed scorer inputs so audit code cannot turn
    unexpected output shapes into credit.
    """

    if result.status != "completed" or result.job_id != job.job_id:
        return 0

    if job.job_type == "echo":
        return ECHO_CONTRIBUTION_UNITS if isinstance(result.output, str) else 0
    if job.job_type == "text_stats":
        return _score_text_stats(result.output)
    if job.job_type == "keyword_extract":
        return _score_keyword_extract(result.output)
    if job.job_type == "text_chunk":
        return _score_text_chunk(result.output)
    if job.job_type == "text_embed":
        return _score_text_embed(result.output)
    if job.job_type == "extractive_summary":
        return _score_extractive_summary(result.output)
    return 0


def _score_text_stats(output: Any) -> int:
    if not isinstance(output, dict):
        return 0
    character_count = output.get("character_count")
    if not _non_negative_int(character_count):
        return 0
    bucket_units = _ceil_div(cast(int, character_count), TEXT_STATS_CHARACTER_BUCKET)
    return _cap_units(1 + bucket_units, TEXT_STATS_MAX_UNITS)


def _score_keyword_extract(output: Any) -> int:
    if not isinstance(output, dict):
        return 0
    keywords = output.get("keywords")
    if not isinstance(keywords, list):
        return 0
    unique_terms = {
        keyword.get("term")
        for keyword in keywords
        if isinstance(keyword, dict) and isinstance(keyword.get("term"), str)
    }
    if len(unique_terms) != len(keywords):
        return 0
    bucket_units = _ceil_div(len(unique_terms), KEYWORD_EXTRACT_KEYWORDS_PER_UNIT)
    return _cap_units(1 + bucket_units, KEYWORD_EXTRACT_MAX_UNITS)


def _score_text_chunk(output: Any) -> int:
    if not isinstance(output, dict):
        return 0
    chunk_count = output.get("chunk_count")
    chunks = output.get("chunks")
    if not _non_negative_int(chunk_count) or not isinstance(chunks, list):
        return 0
    if len(chunks) != chunk_count:
        return 0
    bucket_units = _ceil_div(cast(int, chunk_count), TEXT_CHUNK_CHUNKS_PER_UNIT)
    return _cap_units(1 + bucket_units, TEXT_CHUNK_MAX_UNITS)


def _score_text_embed(output: Any) -> int:
    if not isinstance(output, dict):
        return 0
    token_count = output.get("token_count")
    dimensions = output.get("dimensions")
    vector = output.get("vector")
    if not _non_negative_int(token_count) or not _non_negative_int(dimensions):
        return 0
    if not isinstance(vector, list) or len(vector) != dimensions:
        return 0
    token_units = _ceil_div(cast(int, token_count), TEXT_EMBED_TOKENS_PER_UNIT)
    dimension_units = _ceil_div(cast(int, dimensions), TEXT_EMBED_DIMENSIONS_PER_UNIT)
    return _cap_units(1 + token_units + dimension_units, TEXT_EMBED_MAX_UNITS)


def _score_extractive_summary(output: Any) -> int:
    if not isinstance(output, dict):
        return 0
    summary = output.get("summary")
    sentences = output.get("sentences")
    sentence_count = output.get("sentence_count")
    source_sentence_count = output.get("source_sentence_count")
    character_count = output.get("character_count")
    if not isinstance(summary, str) or not isinstance(sentences, list):
        return 0
    if not _non_negative_int(sentence_count) or not _non_negative_int(
        source_sentence_count
    ):
        return 0
    if not _non_negative_int(character_count):
        return 0
    if len(sentences) != sentence_count or cast(int, sentence_count) > cast(
        int, source_sentence_count
    ):
        return 0
    for sentence in sentences:
        if not isinstance(sentence, dict):
            return 0
        if not _non_negative_int(sentence.get("index")):
            return 0
        if not isinstance(sentence.get("text"), str):
            return 0
        if not _non_negative_int(sentence.get("score")):
            return 0
        if not _non_negative_int(sentence.get("token_count")):
            return 0
    bucket_units = _ceil_div(
        cast(int, sentence_count), EXTRACTIVE_SUMMARY_SENTENCES_PER_UNIT
    )
    return _cap_units(1 + bucket_units, EXTRACTIVE_SUMMARY_MAX_UNITS)


def _ceil_div(value: int, bucket_size: int) -> int:
    if value == 0:
        return 0
    return ceil(value / bucket_size)


def _cap_units(units: int, cap: int) -> int:
    return max(0, min(units, cap))


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
