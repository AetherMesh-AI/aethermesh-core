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

        self.assertEqual(missing.status, "failed")
        self.assertEqual(missing.contribution_units, 0)
        self.assertEqual(missing.error, "text_stats payload requires string field: text")
        self.assertEqual(non_string.status, "failed")
        self.assertEqual(non_string.contribution_units, 0)
        self.assertEqual(non_string.error, "text_stats payload requires string field: text")

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

    def test_keyword_extract_sorting_limit_and_stopwords_are_deterministic(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))
        result = runner.run(
            Job(
                job_id="keyword-sort",
                job_type="keyword_extract",
                payload={"text": "The beta alpha beta, gamma alpha beta and delta", "limit": 3},
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
            Job(job_id="keyword-default", job_type="keyword_extract", payload={"text": "one two three"})
        )

        self.assertEqual(result.status, "completed")
        self.assertEqual(len(result.output["keywords"]), 3)

    def test_keyword_extract_malformed_payload_fails_predictably(self) -> None:
        runner = LocalRunner(NodeIdentity(node_id="local-test-node"))

        cases = [
            Job(job_id="missing", job_type="keyword_extract", payload={}),
            Job(job_id="blank", job_type="keyword_extract", payload={"text": "  "}),
            Job(job_id="non-int-limit", job_type="keyword_extract", payload={"text": "hello", "limit": "5"}),
            Job(job_id="zero-limit", job_type="keyword_extract", payload={"text": "hello", "limit": 0}),
            Job(job_id="large-limit", job_type="keyword_extract", payload={"text": "hello", "limit": 51}),
        ]

        for job in cases:
            with self.subTest(job_id=job.job_id):
                result = runner.run(job)
                self.assertEqual(result.status, "failed")
                self.assertIsNone(result.output)
                self.assertEqual(result.contribution_units, 0)
                self.assertIsInstance(result.error, str)
                self.assertTrue(result.error.startswith("keyword_extract payload requires"))


if __name__ == "__main__":
    unittest.main()
