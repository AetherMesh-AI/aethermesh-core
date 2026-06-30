import unittest

from aethermesh_core.models import Job, NodeIdentity
from aethermesh_core.runner import LocalRunner


class LocalRunnerTests(unittest.TestCase):
    def test_echo_job_completes_and_serializes_expected_shape(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        job = Job(
            job_id="job-echo-1",
            job_type="echo",
            payload={"message": "hello mesh"},
        )

        result = runner.run(job)
        serialized = result.to_dict()

        self.assertEqual(serialized["job_id"], "job-echo-1")
        self.assertEqual(serialized["node_id"], "local-test-node")
        self.assertEqual(serialized["status"], "completed")
        self.assertEqual(serialized["output"], "hello mesh")
        self.assertIsNone(serialized["error"])
        self.assertGreater(serialized["contribution_units"], 0)
        self.assertEqual(
            set(serialized),
            {
                "job_id",
                "node_id",
                "status",
                "output",
                "error",
                "contribution_units",
            },
        )

    def test_echo_missing_message_defaults_to_empty_string(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(Job(job_id="echo-empty", job_type="echo", payload={}))

        self.assertEqual(
            result.to_dict(),
            {
                "job_id": "echo-empty",
                "node_id": "local-test-node",
                "status": "completed",
                "output": "",
                "error": None,
                "contribution_units": 1,
            },
        )

    def test_unsupported_job_type_fails_predictably(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        job = Job(job_id="job-nope-1", job_type="unsupported", payload={})

        result = runner.run(job)

        self.assertEqual(result.job_id, "job-nope-1")
        self.assertEqual(result.node_id, "local-test-node")
        self.assertEqual(result.status, "failed")
        self.assertIsNone(result.output)
        self.assertEqual(result.error, "Unsupported job type: unsupported")
        self.assertEqual(result.contribution_units, 0)

    def test_text_stats_job_completes_with_deterministic_output(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        job = Job(
            job_id="job-text-stats-1",
            job_type="text_stats",
            payload={"text": "hello mesh\nhello node"},
        )

        result = runner.run(job)

        self.assertEqual(result.job_id, "job-text-stats-1")
        self.assertEqual(result.node_id, "local-test-node")
        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "character_count": len("hello mesh\nhello node"),
                "word_count": 4,
                "line_count": 2,
                "normalized_preview": "hello mesh hello node",
            },
        )
        self.assertIsNone(result.error)
        self.assertEqual(result.contribution_units, 1)

    def test_text_stats_preview_is_truncated_to_80_characters(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        text = " ".join(["word"] * 30)

        result = runner.run(
            Job(job_id="stats-preview", job_type="text_stats", payload={"text": text})
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output["normalized_preview"], " ".join(text.split())[:80]
        )
        self.assertEqual(len(result.output["normalized_preview"]), 80)

    def test_text_stats_empty_text_completes_deterministically(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        job = Job(job_id="job-text-empty", job_type="text_stats", payload={"text": ""})

        result = runner.run(job)

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "character_count": 0,
                "word_count": 0,
                "line_count": 1,
                "normalized_preview": "",
            },
        )
        self.assertEqual(result.contribution_units, 1)

    def test_text_stats_malformed_payload_fails_predictably(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))

        missing = runner.run(Job(job_id="missing", job_type="text_stats", payload={}))
        non_string = runner.run(
            Job(job_id="non-string", job_type="text_stats", payload={"text": 123})
        )

        self.assertEqual(missing.job_id, "missing")
        self.assertEqual(missing.node_id, "local-test-node")
        self.assertEqual(missing.status, "failed")
        self.assertEqual(missing.contribution_units, 0)
        self.assertEqual(
            missing.error, "text_stats payload requires string field: text"
        )
        self.assertEqual(non_string.status, "failed")
        self.assertEqual(non_string.contribution_units, 0)
        self.assertEqual(
            non_string.error, "text_stats payload requires string field: text"
        )

    def test_keyword_extract_completes_with_deterministic_output(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        job = Job(
            job_id="keyword-1",
            job_type="keyword_extract",
            payload={
                "text": "AetherMesh nodes process useful local work for the mesh.",
                "limit": 5,
            },
        )

        result = runner.run(job)

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "keywords": [
                    {"term": "aethermesh", "count": 1},
                    {"term": "local", "count": 1},
                    {"term": "mesh", "count": 1},
                    {"term": "nodes", "count": 1},
                    {"term": "process", "count": 1},
                ],
                "unique_terms": 7,
                "total_terms": 7,
            },
        )
        self.assertEqual(result.contribution_units, 1)

    def test_keyword_extract_sorting_limit_and_stopwords_are_deterministic(
        self,
    ) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="keyword-sort",
                job_type="keyword_extract",
                payload={
                    "text": "The beta alpha beta, gamma alpha beta and delta",
                    "limit": 3,
                },
            )
        )

        self.assertEqual(
            result.output,
            {
                "keywords": [
                    {"term": "beta", "count": 3},
                    {"term": "alpha", "count": 2},
                    {"term": "delta", "count": 1},
                ],
                "unique_terms": 4,
                "total_terms": 7,
            },
        )

    def test_keyword_extract_uses_default_limit(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="keyword-default",
                job_type="keyword_extract",
                payload={"text": "one two three"},
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.output["keywords"]), 3)

    def test_keyword_extract_accepts_min_and_max_limits(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        for limit in (1, 50):
            with self.subTest(limit=limit):
                result = runner.run(
                    Job(
                        job_id=f"keyword-limit-{limit}",
                        job_type="keyword_extract",
                        payload={"text": "alpha beta gamma", "limit": limit},
                    )
                )
                self.assertEqual(result.status, "completed")
                self.assertLessEqual(len(result.output["keywords"]), limit)

    def test_keyword_extract_malformed_payload_fails_predictably(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))

        cases = [
            Job(job_id="missing", job_type="keyword_extract", payload={}),
            Job(job_id="blank", job_type="keyword_extract", payload={"text": "  "}),
            Job(
                job_id="non-int-limit",
                job_type="keyword_extract",
                payload={"text": "hello", "limit": "5"},
            ),
            Job(
                job_id="zero-limit",
                job_type="keyword_extract",
                payload={"text": "hello", "limit": 0},
            ),
            Job(
                job_id="large-limit",
                job_type="keyword_extract",
                payload={"text": "hello", "limit": 51},
            ),
        ]

        for job in cases:
            with self.subTest(job_id=job.job_id):
                result = runner.run(job)
                self.assertEqual(result.status, "failed")
                self.assertIsNone(result.output)
                self.assertEqual(result.contribution_units, 0)
                self.assertIsInstance(result.error, str)
                assert result.error is not None
                self.assertTrue(
                    result.error.startswith("keyword_extract payload requires")
                )

    def test_text_chunk_completes_with_deterministic_output(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="chunk-1",
                job_type="text_chunk",
                payload={"text": "alpha beta gamma", "max_chars": 10},
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "chunks": [
                    {"index": 0, "text": "alpha beta", "character_count": 10},
                    {"index": 1, "text": " gamma", "character_count": 6},
                ],
                "chunk_count": 2,
                "character_count": 16,
            },
        )
        self.assertEqual(result.contribution_units, 1)

    def test_text_chunk_splits_on_space_immediately_before_hard_end(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))

        result = runner.run(
            Job(
                job_id="chunk-space-before-end",
                job_type="text_chunk",
                payload={"text": "abcd efgh", "max_chars": 6},
            )
        )

        self.assertEqual(
            result.output,
            {
                "chunks": [
                    {"index": 0, "text": "abcd ", "character_count": 5},
                    {"index": 1, "text": "efgh", "character_count": 4},
                ],
                "chunk_count": 2,
                "character_count": 9,
            },
        )

    def test_text_chunk_empty_text_returns_zero_chunks(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(job_id="chunk-empty", job_type="text_chunk", payload={"text": ""})
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output, {"chunks": [], "chunk_count": 0, "character_count": 0}
        )
        self.assertEqual(result.contribution_units, 1)

    def test_text_chunk_preserves_whitespace_and_long_words(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="chunk-whitespace",
                job_type="text_chunk",
                payload={"text": "  alpha  superlongword", "max_chars": 8},
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "chunks": [
                    {"index": 0, "text": "  alpha ", "character_count": 8},
                    {"index": 1, "text": " ", "character_count": 1},
                    {"index": 2, "text": "superlon", "character_count": 8},
                    {"index": 3, "text": "gword", "character_count": 5},
                ],
                "chunk_count": 4,
                "character_count": 22,
            },
        )

    def test_text_chunk_uses_default_max_chars(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        text = "x" * 121
        result = runner.run(
            Job(job_id="chunk-default", job_type="text_chunk", payload={"text": text})
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output["chunk_count"], 2)
        self.assertEqual(result.output["chunks"][0]["character_count"], 120)
        self.assertEqual(result.output["character_count"], 121)

    def test_text_chunk_accepts_min_and_max_chunk_sizes(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        for max_chars in (1, 1000):
            with self.subTest(max_chars=max_chars):
                result = runner.run(
                    Job(
                        job_id=f"chunk-boundary-{max_chars}",
                        job_type="text_chunk",
                        payload={"text": "ab", "max_chars": max_chars},
                    )
                )
                self.assertEqual(result.status, "completed")
                self.assertEqual(result.contribution_units, 1)

    def test_text_chunk_malformed_payload_fails_predictably(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))

        cases = [
            Job(job_id="missing", job_type="text_chunk", payload={}),
            Job(job_id="non-string", job_type="text_chunk", payload={"text": 123}),
            Job(
                job_id="non-int-max",
                job_type="text_chunk",
                payload={"text": "hello", "max_chars": "5"},
            ),
            Job(
                job_id="bool-max",
                job_type="text_chunk",
                payload={"text": "hello", "max_chars": True},
            ),
            Job(
                job_id="zero-max",
                job_type="text_chunk",
                payload={"text": "hello", "max_chars": 0},
            ),
            Job(
                job_id="large-max",
                job_type="text_chunk",
                payload={"text": "hello", "max_chars": 1001},
            ),
        ]

        for job in cases:
            with self.subTest(job_id=job.job_id):
                result = runner.run(job)
                self.assertEqual(result.status, "failed")
                self.assertIsNone(result.output)
                self.assertEqual(result.contribution_units, 0)
                self.assertIsInstance(result.error, str)
                error = result.error
                self.assertIsInstance(error, str)
                self.assertTrue(str(error).startswith("text_chunk payload requires"))

    def test_text_embed_completes_with_deterministic_output(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="embed-1",
                job_type="text_embed",
                payload={
                    "text": "AetherMesh nodes process useful local work for the mesh.",
                    "dimensions": 8,
                },
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "dimensions": 8,
                "token_count": 9,
                "unique_terms": 9,
                "vector": [4, 1, 1, 1, 0, 0, 1, 1],
            },
        )
        self.assertEqual(result.contribution_units, 1)

    def test_text_embed_uses_default_dimensions(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="embed-default",
                job_type="text_embed",
                payload={"text": "one two three"},
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "dimensions": 8,
                "token_count": 3,
                "unique_terms": 3,
                "vector": [1, 0, 2, 0, 0, 0, 0, 0],
            },
        )

    def test_text_embed_accepts_min_and_max_dimensions(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        for dimensions in (2, 64):
            with self.subTest(dimensions=dimensions):
                result = runner.run(
                    Job(
                        job_id=f"embed-boundary-{dimensions}",
                        job_type="text_embed",
                        payload={"text": "alpha beta", "dimensions": dimensions},
                    )
                )
                self.assertEqual(result.status, "completed")
                self.assertEqual(result.output["dimensions"], dimensions)
                self.assertEqual(len(result.output["vector"]), dimensions)

    def test_text_embed_malformed_payload_fails_predictably(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))

        cases = [
            Job(job_id="missing", job_type="text_embed", payload={}),
            Job(job_id="blank", job_type="text_embed", payload={"text": "  "}),
            Job(job_id="non-string", job_type="text_embed", payload={"text": 123}),
            Job(
                job_id="non-int-dimensions",
                job_type="text_embed",
                payload={"text": "hello", "dimensions": "8"},
            ),
            Job(
                job_id="bool-dimensions",
                job_type="text_embed",
                payload={"text": "hello", "dimensions": True},
            ),
            Job(
                job_id="small-dimensions",
                job_type="text_embed",
                payload={"text": "hello", "dimensions": 1},
            ),
            Job(
                job_id="large-dimensions",
                job_type="text_embed",
                payload={"text": "hello", "dimensions": 65},
            ),
        ]

        for job in cases:
            with self.subTest(job_id=job.job_id):
                result = runner.run(job)
                self.assertEqual(result.status, "failed")
                self.assertIsNone(result.output)
                self.assertEqual(result.contribution_units, 0)
                self.assertIsInstance(result.error, str)
                self.assertTrue(
                    str(result.error).startswith("text_embed payload requires")
                )

    def test_extractive_summary_completes_with_deterministic_output(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="summary-1",
                job_type="extractive_summary",
                payload={
                    "text": "Alpha mesh helps nodes. Beta mesh mesh validates work. Gamma work work supports nodes! Tiny. Delta work reports local work.",
                    "max_sentences": 2,
                },
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "summary": "Beta mesh mesh validates work. Gamma work work supports nodes!",
                "sentences": [
                    {
                        "index": 1,
                        "text": "Beta mesh mesh validates work.",
                        "score": 13,
                        "token_count": 5,
                    },
                    {
                        "index": 2,
                        "text": "Gamma work work supports nodes!",
                        "score": 14,
                        "token_count": 5,
                    },
                ],
                "sentence_count": 2,
                "source_sentence_count": 5,
                "character_count": 123,
            },
        )
        self.assertEqual(result.contribution_units, 1)

    def test_extractive_summary_uses_default_and_original_order_tie_breaks(
        self,
    ) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="summary-default",
                job_type="extractive_summary",
                payload={"text": "One alpha. Two beta. Three gamma. Four delta."},
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.output["sentence_count"], 3)
        self.assertEqual(
            [sentence["index"] for sentence in result.output["sentences"]],
            [0, 1, 2],
        )
        self.assertEqual(result.output["summary"], "One alpha. Two beta. Three gamma.")

    def test_extractive_summary_splits_on_newlines_and_is_deterministic(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        job = Job(
            job_id="summary-newline",
            job_type="extractive_summary",
            payload={
                "text": "First repeated alpha\nSecond repeated repeated beta\nThird gamma.",
                "max_sentences": 2,
            },
        )

        first = runner.run(job)
        second = runner.run(job)

        self.assertEqual(first.output, second.output)
        self.assertEqual(
            first.output["summary"],
            "First repeated alpha Second repeated repeated beta",
        )
        self.assertEqual(first.output["source_sentence_count"], 3)

    def test_extractive_summary_accepts_min_and_max_sentence_limits(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        for max_sentences in (1, 10):
            with self.subTest(max_sentences=max_sentences):
                result = runner.run(
                    Job(
                        job_id=f"summary-boundary-{max_sentences}",
                        job_type="extractive_summary",
                        payload={
                            "text": "Alpha. Beta. Gamma.",
                            "max_sentences": max_sentences,
                        },
                    )
                )
                self.assertEqual(result.status, "completed")
                self.assertLessEqual(result.output["sentence_count"], max_sentences)

    def test_extractive_summary_malformed_payload_fails_predictably(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        cases = [
            Job(job_id="missing", job_type="extractive_summary", payload={}),
            Job(job_id="blank", job_type="extractive_summary", payload={"text": "  "}),
            Job(
                job_id="non-string",
                job_type="extractive_summary",
                payload={"text": 123},
            ),
            Job(
                job_id="zero-max-sentences",
                job_type="extractive_summary",
                payload={"text": "hello", "max_sentences": 0},
            ),
            Job(
                job_id="large-max-sentences",
                job_type="extractive_summary",
                payload={"text": "hello", "max_sentences": 11},
            ),
            Job(
                job_id="float-max-sentences",
                job_type="extractive_summary",
                payload={"text": "hello", "max_sentences": 1.5},
            ),
            Job(
                job_id="string-max-sentences",
                job_type="extractive_summary",
                payload={"text": "hello", "max_sentences": "2"},
            ),
            Job(
                job_id="bool-max-sentences",
                job_type="extractive_summary",
                payload={"text": "hello", "max_sentences": True},
            ),
        ]

        for job in cases:
            with self.subTest(job_id=job.job_id):
                result = runner.run(job)
                self.assertEqual(result.status, "failed")
                self.assertIsNone(result.output)
                self.assertEqual(result.contribution_units, 0)
                self.assertIsInstance(result.error, str)
                self.assertTrue(
                    str(result.error).startswith("extractive_summary payload requires")
                )


if __name__ == "__main__":
    unittest.main()
