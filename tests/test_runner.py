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


if __name__ == "__main__":
    unittest.main()
