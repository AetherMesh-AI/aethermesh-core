import unittest

from aethermesh_core.models import Job
from aethermesh_core.scheduler import JobAssignment, NodeStatus, ScheduledNode
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
            [message["sender_node_id"] for message in result["messages"][:3]],
            ["local-scheduler", "node-a", "local-ledger"],
        )
        self.assertEqual(
            [message["recipient_node_id"] for message in result["messages"][:3]],
            ["node-a", "local-ledger", "node-a"],
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
                    "validation": "ok",
                    "valid": True,
                    "contribution_units": 1,
                },
            ],
        )

    def test_simulation_preserves_default_output_with_scheduler(self) -> None:
        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "one"}),
            Job(job_id="echo-2", job_type="echo", payload={"message": "two"}),
        ]

        result = run_local_simulation(["node-a", "node-b"], jobs)
        result_dict = result.to_dict()

        self.assertTrue(
            all(isinstance(assignment, JobAssignment) for assignment in result.assignments)
        )
        self.assertEqual(
            result_dict["assignments"],
            [
                {"job_id": "echo-1", "node_id": "node-a"},
                {"job_id": "echo-2", "node_id": "node-b"},
            ],
        )
        self.assertNotIn("accounted_results", result_dict)

    def test_simulation_exposes_validation_gated_accounted_results(self) -> None:
        jobs = [Job(job_id="echo-missing-message", job_type="echo", payload={})]

        result = run_local_simulation(["node-a"], jobs)

        self.assertEqual(len(result.accounted_results), 1)
        self.assertEqual(result.results[0].contribution_units, 1)
        self.assertEqual(result.accounted_results[0].status, "completed")
        self.assertEqual(result.accounted_results[0].contribution_units, 0)

    def test_node_roster_includes_offline_nodes_without_assignments(self) -> None:
        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "one"}),
            Job(job_id="echo-2", job_type="echo", payload={"message": "two"}),
            Job(job_id="echo-3", job_type="echo", payload={"message": "three"}),
        ]

        result = run_local_simulation(
            [
                ScheduledNode("node-a", NodeStatus.AVAILABLE),
                ScheduledNode("node-b", NodeStatus.OFFLINE),
                ScheduledNode("node-c", NodeStatus.AVAILABLE),
            ],
            jobs,
        ).to_dict()

        self.assertEqual(result["nodes"], ["node-a", "node-b", "node-c"])
        self.assertEqual(
            result["assignments"],
            [
                {"job_id": "echo-1", "node_id": "node-a"},
                {"job_id": "echo-2", "node_id": "node-c"},
                {"job_id": "echo-3", "node_id": "node-a"},
            ],
        )
        self.assertEqual(
            result["node_roster"],
            [
                {
                    "node_id": "node-a",
                    "status": "available",
                    "assigned_jobs": 2,
                    "contribution_units": 2,
                },
                {
                    "node_id": "node-b",
                    "status": "offline",
                    "assigned_jobs": 0,
                    "contribution_units": 0,
                },
                {
                    "node_id": "node-c",
                    "status": "available",
                    "assigned_jobs": 1,
                    "contribution_units": 1,
                },
            ],
        )
        self.assertEqual(result["summaries"][1]["node_id"], "node-b")
        self.assertEqual(result["summaries"][1]["results"], 0)
        self.assertEqual(result["totals"]["contribution_units"], 3)

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
            result["validation_summary"], {"valid": 3, "invalid": 0, "unsupported": 0}
        )
        self.assertEqual(
            result["validations"],
            [
                {
                    "job_id": "echo-1",
                    "result_job_id": "echo-1",
                    "valid": True,
                    "reason": "ok",
                },
                {
                    "job_id": "echo-2",
                    "result_job_id": "echo-2",
                    "valid": True,
                    "reason": "ok",
                },
                {
                    "job_id": "echo-3",
                    "result_job_id": "echo-3",
                    "valid": True,
                    "reason": "ok",
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
                "valid_results": 3,
                "invalid_results": 0,
                "unsupported_results": 0,
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
        self.assertEqual(result["validations"][1]["valid"], False)
        self.assertEqual(result["validations"][1]["reason"], "unsupported_job_type")
        self.assertEqual(
            result["validation_summary"], {"valid": 1, "invalid": 1, "unsupported": 1}
        )
        self.assertEqual(result["totals"]["completed_jobs"], 1)
        self.assertEqual(result["totals"]["failed_jobs"], 1)
        self.assertEqual(result["totals"]["valid_results"], 1)
        self.assertEqual(result["totals"]["invalid_results"], 1)
        self.assertEqual(result["totals"]["unsupported_results"], 1)
        self.assertEqual(result["totals"]["contribution_units"], 1)

    def test_invalid_completed_echo_result_is_visible_but_earns_zero_units(self) -> None:
        jobs = [Job(job_id="echo-missing-message", job_type="echo", payload={})]

        result = run_local_simulation(["node-a"], jobs).to_dict()

        self.assertEqual(result["results"][0]["status"], "completed")
        self.assertEqual(result["results"][0]["contribution_units"], 1)
        self.assertEqual(
            result["validations"][0],
            {
                "job_id": "echo-missing-message",
                "result_job_id": "echo-missing-message",
                "valid": False,
                "reason": "missing_payload_message",
            },
        )
        self.assertEqual(
            result["validation_summary"], {"valid": 0, "invalid": 1, "unsupported": 0}
        )
        self.assertEqual(result["summaries"][0]["completed_jobs"], 1)
        self.assertEqual(result["summaries"][0]["contribution_units"], 0)
        self.assertEqual(result["messages"][2]["payload"]["valid"], False)
        self.assertEqual(result["messages"][2]["payload"]["validation"], "missing_payload_message")
        self.assertEqual(result["messages"][2]["payload"]["contribution_units"], 0)
        self.assertEqual(result["totals"]["completed_jobs"], 1)
        self.assertEqual(result["totals"]["valid_results"], 0)
        self.assertEqual(result["totals"]["invalid_results"], 1)
        self.assertEqual(result["totals"]["contribution_units"], 0)

    def test_empty_node_list_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "node_ids must contain at least one node"):
            run_local_simulation([], [Job(job_id="echo-1", job_type="echo")])

    def test_text_stats_contribution_is_gated_by_validation(self) -> None:
        jobs = [
            Job(
                job_id="text-stats-1",
                job_type="text_stats",
                payload={"text": "hello mesh\nhello node"},
            ),
            Job(job_id="text-stats-bad", job_type="text_stats", payload={"text": 123}),
        ]

        result = run_local_simulation(["node-a"], jobs).to_dict()

        self.assertEqual(result["results"][0]["status"], "completed")
        self.assertEqual(
            result["results"][0]["output"],
            {
                "character_count": len("hello mesh\nhello node"),
                "word_count": 4,
                "line_count": 2,
                "normalized_preview": "hello mesh hello node",
            },
        )
        self.assertEqual(result["results"][1]["status"], "failed")
        self.assertEqual(result["validations"][0]["valid"], True)
        self.assertEqual(result["validations"][1]["valid"], False)
        self.assertEqual(result["validations"][1]["reason"], "result_not_completed")
        self.assertEqual(result["summaries"][0]["completed_jobs"], 1)
        self.assertEqual(result["summaries"][0]["failed_jobs"], 1)
        self.assertEqual(result["summaries"][0]["contribution_units"], 1)
        self.assertEqual(result["totals"]["contribution_units"], 1)


if __name__ == "__main__":
    unittest.main()
