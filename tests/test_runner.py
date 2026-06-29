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


if __name__ == "__main__":
    unittest.main()
