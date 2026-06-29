import unittest

from aethermesh_core.models import Job
from aethermesh_core.simulation import run_local_simulation


class LocalSimulationTests(unittest.TestCase):
    def test_jobs_are_assigned_round_robin_by_input_order(self) -> None:
        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "one"}),
            Job(job_id="echo-2", job_type="echo", payload={"message": "two"}),
            Job(job_id="echo-3", job_type="echo", payload={"message": "three"}),
        ]

        result = run_local_simulation(["node-a", "node-b"], jobs).to_dict()

        self.assertEqual(result["nodes"], ["node-a", "node-b"])
        self.assertEqual(
            result["assignments"],
            [
                {"job_id": "echo-1", "node_id": "node-a"},
                {"job_id": "echo-2", "node_id": "node-b"},
                {"job_id": "echo-3", "node_id": "node-a"},
            ],
        )
        self.assertEqual(
            [(item["job_id"], item["node_id"]) for item in result["results"]],
            [("echo-1", "node-a"), ("echo-2", "node-b"), ("echo-3", "node-a")],
        )
        self.assertEqual(
            [message["message_id"] for message in result["messages"]],
            [
                "msg-0001",
                "msg-0002",
                "msg-0003",
                "msg-0004",
                "msg-0005",
                "msg-0006",
                "msg-0007",
                "msg-0008",
                "msg-0009",
            ],
        )
        self.assertEqual(
            [message["message_type"] for message in result["messages"]],
            [
                "job_assigned",
                "job_result_reported",
                "contribution_recorded",
                "job_assigned",
                "job_result_reported",
                "contribution_recorded",
                "job_assigned",
                "job_result_reported",
                "contribution_recorded",
            ],
        )
        self.assertEqual(
            [message["correlation_id"] for message in result["messages"]],
            [
                "echo-1",
                "echo-1",
                "echo-1",
                "echo-2",
                "echo-2",
                "echo-2",
                "echo-3",
                "echo-3",
                "echo-3",
            ],
        )
        self.assertEqual(
            [message["payload"] for message in result["messages"][:3]],
            [
                {"job_id": "echo-1", "job_type": "echo", "node_id": "node-a"},
                {
                    "job_id": "echo-1",
                    "status": "completed",
                    "success": True,
                    "output": "one",
                    "error": None,
                },
                {
                    "job_id": "echo-1",
                    "node_id": "node-a",
                    "status": "completed",
                    "contribution_units": 1,
                },
            ],
        )

    def test_successful_echo_jobs_contribute_units_and_totals(self) -> None:
        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "one"}),
            Job(job_id="echo-2", job_type="echo", payload={"message": "two"}),
            Job(job_id="echo-3", job_type="echo", payload={"message": "three"}),
        ]

        result = run_local_simulation(["node-a", "node-b"], jobs).to_dict()

        self.assertEqual(
            result["summaries"],
            [
                {
                    "node_id": "node-a",
                    "completed_jobs": 2,
                    "failed_jobs": 0,
                    "results": 2,
                    "contribution_units": 2,
                },
                {
                    "node_id": "node-b",
                    "completed_jobs": 1,
                    "failed_jobs": 0,
                    "results": 1,
                    "contribution_units": 1,
                },
            ],
        )
        self.assertEqual(
            result["totals"],
            {
                "nodes": 2,
                "jobs": 3,
                "results": 3,
                "completed_jobs": 3,
                "failed_jobs": 0,
                "contribution_units": 3,
            },
        )

    def test_unsupported_jobs_are_recorded_as_failures_with_zero_units(self) -> None:
        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "one"}),
            Job(job_id="bad-1", job_type="unsupported", payload={}),
        ]

        result = run_local_simulation(["node-a", "node-b"], jobs).to_dict()

        self.assertEqual(result["results"][1]["job_id"], "bad-1")
        self.assertEqual(result["results"][1]["node_id"], "node-b")
        self.assertEqual(result["results"][1]["status"], "failed")
        self.assertEqual(result["results"][1]["contribution_units"], 0)
        self.assertEqual(result["summaries"][1]["failed_jobs"], 1)
        self.assertEqual(result["summaries"][1]["contribution_units"], 0)
        self.assertEqual(result["totals"]["completed_jobs"], 1)
        self.assertEqual(result["totals"]["failed_jobs"], 1)
        self.assertEqual(result["totals"]["contribution_units"], 1)

    def test_empty_node_list_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "node_ids must contain at least one node"):
            run_local_simulation([], [Job(job_id="echo-1", job_type="echo")])


if __name__ == "__main__":
    unittest.main()
