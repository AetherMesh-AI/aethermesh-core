import unittest
from unittest.mock import patch

from aethermesh_core.models import Job
from aethermesh_core.node_service import LocalNodeService
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
            [f"msg-{index:04d}" for index in range(1, 15)],
        )
        self.assertEqual(
            [message["message_type"] for message in result["messages"]],
            [
                "node_heartbeat",
                "node_heartbeat",
                "job_assigned",
                "job_result_reported",
                "job_validated",
                "contribution_recorded",
                "job_assigned",
                "job_result_reported",
                "job_validated",
                "contribution_recorded",
                "job_assigned",
                "job_result_reported",
                "job_validated",
                "contribution_recorded",
            ],
        )
        self.assertEqual(
            [message["correlation_id"] for message in result["messages"]],
            [
                None,
                None,
                "echo-1",
                "echo-1",
                "echo-1",
                "echo-1",
                "echo-2",
                "echo-2",
                "echo-2",
                "echo-2",
                "echo-3",
                "echo-3",
                "echo-3",
                "echo-3",
            ],
        )
        self.assertEqual(
            [message["payload"] for message in result["messages"][:2]],
            [
                {
                    "node_id": "node-a",
                    "status": "available",
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                },
                {
                    "node_id": "node-b",
                    "status": "available",
                    "heartbeat_sequence": 2,
                    "heartbeat_count": 1,
                },
            ],
        )
        self.assertEqual(
            [message["sender_node_id"] for message in result["messages"][2:5]],
            ["local-scheduler", "node-a", "node-a"],
        )
        self.assertEqual(
            [message["recipient_node_id"] for message in result["messages"][2:5]],
            ["node-a", "local-ledger", "local-ledger"],
        )
        self.assertEqual(
            [message["payload"] for message in result["messages"][2:6]],
            [
                {
                    "job_id": "echo-1",
                    "job_type": "echo",
                    "payload": {"message": "one"},
                    "node_id": "node-a",
                },
                {
                    "job_id": "echo-1",
                    "status": "completed",
                    "success": True,
                    "output": "one",
                    "error": None,
                    "contribution_units": 1,
                },
                {
                    "job_id": "echo-1",
                    "node_id": "node-a",
                    "assignment_message_id": "msg-0003",
                    "result_message_id": "msg-0004",
                    "validator_id": "node-a",
                    "valid": True,
                    "reason": "ok",
                    "contribution_units_after_validation": 1,
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

    def test_assignments_route_by_declared_capability(self) -> None:
        jobs = [
            Job(
                job_id="stats-1", job_type="text_stats", payload={"text": "hello mesh"}
            ),
            Job(job_id="echo-1", job_type="echo", payload={"message": "hello"}),
        ]

        result = run_local_simulation(
            [
                ScheduledNode("node-a", capabilities=("echo",)),
                ScheduledNode("node-b", capabilities=("text_stats",)),
            ],
            jobs,
        ).to_dict()

        self.assertEqual(
            result["assignments"],
            [
                {"job_id": "stats-1", "node_id": "node-b"},
                {"job_id": "echo-1", "node_id": "node-a"},
            ],
        )
        self.assertEqual(
            [entry["capabilities"] for entry in result["node_roster"]],
            [["echo"], ["text_stats"]],
        )

    def test_text_embed_flows_through_simulation_and_validation_accounting(
        self,
    ) -> None:
        jobs = [
            Job(
                job_id="embed-1",
                job_type="text_embed",
                payload={"text": "alpha beta beta", "dimensions": 4},
            )
        ]

        result = run_local_simulation(["node-a"], jobs).to_dict()

        self.assertEqual(
            result["assignments"], [{"job_id": "embed-1", "node_id": "node-a"}]
        )
        self.assertEqual(result["results"][0]["output"]["vector"], [0, 2, 1, 0])
        self.assertEqual(
            result["validations"],
            [
                {
                    "job_id": "embed-1",
                    "result_job_id": "embed-1",
                    "valid": True,
                    "reason": "ok",
                }
            ],
        )
        self.assertEqual(result["totals"]["contribution_units"], 3)

    def test_text_retrieve_flows_through_simulation_and_validation_accounting(
        self,
    ) -> None:
        jobs = [
            Job(
                job_id="retrieve-1",
                job_type="text_retrieve",
                payload={
                    "query": "alpha beta",
                    "documents": [
                        {"id": "doc-b", "text": "alpha only"},
                        {"id": "doc-a", "text": "alpha beta"},
                    ],
                },
            )
        ]

        result = run_local_simulation(["node-a"], jobs).to_dict()

        self.assertEqual(
            result["assignments"], [{"job_id": "retrieve-1", "node_id": "node-a"}]
        )
        self.assertEqual(
            result["results"][0]["output"],
            {
                "query_terms": ["alpha", "beta"],
                "matches": [
                    {
                        "id": "doc-a",
                        "score": 1.0,
                        "matched_term_count": 2,
                        "matched_terms": ["alpha", "beta"],
                    },
                    {
                        "id": "doc-b",
                        "score": 0.5,
                        "matched_term_count": 1,
                        "matched_terms": ["alpha"],
                    },
                ],
            },
        )
        self.assertEqual(result["validations"][0]["valid"], True)
        self.assertEqual(result["totals"]["contribution_units"], 1)

    def test_jobs_are_executed_by_node_service_inbox_processing(self) -> None:
        calls: list[str] = []
        original_process_inbox = LocalNodeService.process_inbox

        def wrapped_process_inbox(self: LocalNodeService):
            calls.append(self.identity.node_id)
            return original_process_inbox(self)

        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "one"}),
            Job(job_id="echo-2", job_type="echo", payload={"message": "two"}),
        ]

        with patch.object(
            LocalNodeService,
            "process_inbox",
            autospec=True,
            side_effect=wrapped_process_inbox,
        ):
            result = run_local_simulation(["node-a", "node-b"], jobs).to_dict()

        self.assertEqual(calls, ["node-a", "node-b"])
        self.assertEqual(result["results"][0]["output"], "one")
        self.assertEqual(result["results"][1]["output"], "two")
        self.assertEqual(
            [message["sender_node_id"] for message in result["messages"][:8]],
            [
                "node-a",
                "node-b",
                "local-scheduler",
                "node-a",
                "node-a",
                "local-ledger",
                "local-scheduler",
                "node-b",
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
            all(
                isinstance(assignment, JobAssignment)
                for assignment in result.assignments
            )
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
        self.assertEqual(result.results[0].contribution_units, 0)
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
                    "capabilities": [
                        "echo",
                        "keyword_extract",
                        "text_chunk",
                        "text_embed",
                        "text_retrieve",
                        "text_stats",
                    ],
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                    "assigned_jobs": 2,
                    "contribution_units": 2,
                },
                {
                    "node_id": "node-b",
                    "status": "offline",
                    "capabilities": [
                        "echo",
                        "keyword_extract",
                        "text_chunk",
                        "text_embed",
                        "text_retrieve",
                        "text_stats",
                    ],
                    "heartbeat_sequence": 0,
                    "heartbeat_count": 0,
                    "assigned_jobs": 0,
                    "contribution_units": 0,
                },
                {
                    "node_id": "node-c",
                    "status": "available",
                    "capabilities": [
                        "echo",
                        "keyword_extract",
                        "text_chunk",
                        "text_embed",
                        "text_retrieve",
                        "text_stats",
                    ],
                    "heartbeat_sequence": 2,
                    "heartbeat_count": 1,
                    "assigned_jobs": 1,
                    "contribution_units": 1,
                },
            ],
        )
        self.assertEqual(result["summaries"][1]["node_id"], "node-b")
        self.assertEqual(result["summaries"][1]["results"], 0)
        self.assertEqual(result["totals"]["contribution_units"], 3)
        heartbeat_messages = [
            message
            for message in result["messages"]
            if message["message_type"] == "node_heartbeat"
        ]
        self.assertEqual(
            [message["sender_node_id"] for message in heartbeat_messages],
            ["node-a", "node-c"],
        )
        self.assertEqual(
            [message["payload"] for message in heartbeat_messages],
            [
                {
                    "node_id": "node-a",
                    "status": "available",
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                },
                {
                    "node_id": "node-c",
                    "status": "available",
                    "heartbeat_sequence": 2,
                    "heartbeat_count": 1,
                },
            ],
        )
        self.assertNotIn(
            "node-b", [message["sender_node_id"] for message in heartbeat_messages]
        )
        self.assertEqual(
            result["messages"][0]["message_type"],
            "node_heartbeat",
        )
        self.assertEqual(
            result["messages"][1]["message_type"],
            "node_heartbeat",
        )
        self.assertEqual(
            result["messages"][2]["message_type"],
            "job_assigned",
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

        result = run_local_simulation(
            [
                ScheduledNode("node-a", capabilities=("echo",)),
                ScheduledNode("node-b", capabilities=("unsupported",)),
            ],
            jobs,
        ).to_dict()

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

    def test_invalid_completed_echo_result_is_visible_but_earns_zero_units(
        self,
    ) -> None:
        jobs = [Job(job_id="echo-missing-message", job_type="echo", payload={})]

        result = run_local_simulation(["node-a"], jobs).to_dict()

        self.assertEqual(result["results"][0]["status"], "completed")
        self.assertEqual(result["results"][0]["contribution_units"], 0)
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
        self.assertEqual(result["messages"][3]["payload"]["valid"], False)
        self.assertEqual(
            result["messages"][3]["payload"]["reason"], "missing_payload_message"
        )
        self.assertEqual(
            result["messages"][3]["payload"]["contribution_units_after_validation"], 0
        )
        self.assertEqual(result["totals"]["completed_jobs"], 1)
        self.assertEqual(result["totals"]["valid_results"], 0)
        self.assertEqual(result["totals"]["invalid_results"], 1)
        self.assertEqual(result["totals"]["contribution_units"], 0)

    def test_empty_node_list_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "node_ids must contain at least one node"
        ):
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
        self.assertEqual(result["summaries"][0]["contribution_units"], 2)
        self.assertEqual(result["totals"]["contribution_units"], 2)


if __name__ == "__main__":
    unittest.main()
