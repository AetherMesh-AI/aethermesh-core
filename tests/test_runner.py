import unittest
from unittest.mock import patch

from aethermesh_core.models import Job, NodeIdentity
from aethermesh_core.runner import LocalRunner, _run_in_local_process, run_local_job


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

    def test_text_retrieve_completes_with_deterministic_output(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="retrieve-1",
                job_type="text_retrieve",
                payload={
                    "query": "Mesh mesh retrieval",
                    "documents": [
                        {"id": "doc-c", "text": "Retrieval systems rank context."},
                        {"id": "doc-b", "text": "Retrieval helps mesh nodes."},
                        {"id": "doc-a", "text": "Mesh workers process tasks."},
                    ],
                    "limit": 3,
                },
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "query_terms": ["mesh", "retrieval"],
                "matches": [
                    {
                        "id": "doc-b",
                        "score": 1.0,
                        "matched_term_count": 2,
                        "matched_terms": ["mesh", "retrieval"],
                    },
                    {
                        "id": "doc-a",
                        "score": 0.5,
                        "matched_term_count": 1,
                        "matched_terms": ["mesh"],
                    },
                    {
                        "id": "doc-c",
                        "score": 0.5,
                        "matched_term_count": 1,
                        "matched_terms": ["retrieval"],
                    },
                ],
            },
        )
        self.assertEqual(result.contribution_units, 1)

    def test_text_retrieve_uses_default_limit_and_stable_id_tiebreaker(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="retrieve-tie",
                job_type="text_retrieve",
                payload={
                    "query": "alpha beta",
                    "documents": [
                        {"id": "doc-c", "text": "alpha only"},
                        {"id": "doc-a", "text": "beta only"},
                        {"id": "doc-b", "text": "no overlap"},
                    ],
                },
            )
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(
            result.output,
            {
                "query_terms": ["alpha", "beta"],
                "matches": [
                    {
                        "id": "doc-a",
                        "score": 0.5,
                        "matched_term_count": 1,
                        "matched_terms": ["beta"],
                    },
                    {
                        "id": "doc-c",
                        "score": 0.5,
                        "matched_term_count": 1,
                        "matched_terms": ["alpha"],
                    },
                    {
                        "id": "doc-b",
                        "score": 0.0,
                        "matched_term_count": 0,
                        "matched_terms": [],
                    },
                ],
            },
        )

    def test_text_retrieve_malformed_payload_fails_predictably(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        valid_documents = [{"id": "doc-1", "text": "alpha beta"}]
        cases = [
            Job(
                job_id="missing-query",
                job_type="text_retrieve",
                payload={"documents": valid_documents},
            ),
            Job(
                job_id="blank-query",
                job_type="text_retrieve",
                payload={"query": "  ", "documents": valid_documents},
            ),
            Job(
                job_id="punct-query",
                job_type="text_retrieve",
                payload={"query": "!!!", "documents": valid_documents},
            ),
            Job(
                job_id="missing-docs",
                job_type="text_retrieve",
                payload={"query": "alpha"},
            ),
            Job(
                job_id="empty-docs",
                job_type="text_retrieve",
                payload={"query": "alpha", "documents": []},
            ),
            Job(
                job_id="bad-limit",
                job_type="text_retrieve",
                payload={"query": "alpha", "documents": valid_documents, "limit": 0},
            ),
            Job(
                job_id="bool-limit",
                job_type="text_retrieve",
                payload={"query": "alpha", "documents": valid_documents, "limit": True},
            ),
            Job(
                job_id="duplicate-id",
                job_type="text_retrieve",
                payload={
                    "query": "alpha",
                    "documents": [
                        {"id": "doc-1", "text": "alpha"},
                        {"id": "doc-1", "text": "beta"},
                    ],
                },
            ),
            Job(
                job_id="bad-doc",
                job_type="text_retrieve",
                payload={"query": "alpha", "documents": [{"id": "doc-1", "text": ""}]},
            ),
        ]

        for job in cases:
            with self.subTest(job_id=job.job_id):
                result = runner.run(job)
                self.assertEqual(result.status, "failed")
                self.assertIsNone(result.output)
                self.assertEqual(result.contribution_units, 0)
                self.assertIsInstance(result.error, str)
                self.assertTrue(str(result.error).startswith("text_retrieve"))


class LocalSafetyRunnerTests(unittest.TestCase):
    def test_declared_timeout_can_complete_and_process_helper_reports_result(
        self,
    ) -> None:
        job = Job(job_id="safe-echo", job_type="echo", payload={"message": "safe"})
        identity = NodeIdentity(node_id="local-test-node")
        result = run_local_job(job, identity, timeout_seconds=1)
        self.assertEqual(result.status, "completed")
        reported: list[object] = []
        queue = type("Queue", (), {"put": lambda _self, item: reported.append(item)})()
        _run_in_local_process(job, identity, queue)
        self.assertEqual(reported[0], result)

    def test_timeout_runner_records_missing_child_result_as_failed(self) -> None:
        class Queue:
            def get(self, *, timeout: int) -> object:
                raise __import__("queue").Empty

            def close(self) -> None:
                pass

        class Process:
            def start(self) -> None:
                pass

            def join(self, timeout: object = None) -> None:
                pass

            def is_alive(self) -> bool:
                return False

        class Context:
            def Queue(self):
                return Queue()

            def Process(self, **_kwargs: object):
                return Process()

        job = Job(job_id="safe-empty", job_type="echo", payload={})
        with patch(
            "aethermesh_core.runner.multiprocessing.get_context", return_value=Context()
        ):
            result = run_local_job(
                job, NodeIdentity(node_id="local-test-node"), timeout_seconds=1
            )
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.contribution_units, 0)


if __name__ == "__main__":
    unittest.main()
