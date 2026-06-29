import contextlib
import io
import json
import unittest

from aethermesh_core.cli import main


class CliTests(unittest.TestCase):
    def test_simulate_local_prints_deterministic_json_shape(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(["simulate-local"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["nodes"], ["local-node-a", "local-node-b"])
        self.assertEqual(
            payload["assignments"],
            [
                {"job_id": "echo-1", "node_id": "local-node-a"},
                {"job_id": "echo-2", "node_id": "local-node-b"},
                {"job_id": "echo-3", "node_id": "local-node-a"},
            ],
        )
        self.assertEqual(len(payload["results"]), 3)
        self.assertEqual(payload["results"][0]["status"], "completed")
        self.assertEqual(len(payload["messages"]), 9)
        self.assertEqual(payload["messages"][0]["message_id"], "msg-0001")
        self.assertEqual(payload["messages"][0]["message_type"], "job_assigned")
        self.assertEqual(payload["messages"][0]["correlation_id"], "echo-1")
        self.assertEqual(payload["messages"][0]["recipient_node_id"], "local-node-a")
        self.assertEqual(payload["messages"][1]["message_type"], "job_result_reported")
        self.assertEqual(payload["messages"][2]["message_type"], "contribution_recorded")
        self.assertEqual(payload["validations"][0]["valid"], True)
        self.assertEqual(payload["validation_summary"], {"valid": 3, "invalid": 0, "unsupported": 0})
        self.assertEqual(payload["summaries"][0]["node_id"], "local-node-a")
        self.assertEqual(
            payload["totals"],
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

    def test_run_demo_command_still_prints_parseable_result(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                [
                    "run-demo",
                    "--node-id",
                    "local-demo-node",
                    "--message",
                    "hello mesh",
                    "--include-ledger",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["result"]["node_id"], "local-demo-node")
        self.assertEqual(payload["result"]["output"], "hello mesh")
        self.assertEqual(payload["validation"]["valid"], True)
        self.assertEqual(payload["validation"]["reason"], "ok")
        self.assertEqual(payload["ledger_summary"]["total_contribution_units"], 1)


if __name__ == "__main__":
    unittest.main()
