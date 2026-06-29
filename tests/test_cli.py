import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

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
                {"job_id": "text-stats-1", "node_id": "local-node-b"},
                {"job_id": "echo-2", "node_id": "local-node-a"},
                {"job_id": "echo-3", "node_id": "local-node-b"},
            ],
        )
        self.assertEqual(len(payload["results"]), 4)
        self.assertEqual(payload["results"][0]["status"], "completed")
        self.assertEqual(payload["results"][1]["output"]["word_count"], 4)
        self.assertEqual(payload["results"][1]["output"]["line_count"], 2)
        self.assertEqual(
            payload["results"][1]["output"]["normalized_preview"],
            "hello mesh hello node",
        )
        self.assertEqual(len(payload["messages"]), 12)
        self.assertEqual(payload["messages"][0]["message_id"], "msg-0001")
        self.assertEqual(payload["messages"][0]["message_type"], "job_assigned")
        self.assertEqual(payload["messages"][0]["correlation_id"], "echo-1")
        self.assertEqual(payload["messages"][0]["recipient_node_id"], "local-node-a")
        self.assertEqual(payload["messages"][1]["message_type"], "job_result_reported")
        self.assertEqual(payload["messages"][2]["message_type"], "contribution_recorded")
        self.assertEqual(payload["validations"][0]["valid"], True)
        self.assertEqual(
            payload["validation_summary"], {"valid": 4, "invalid": 0, "unsupported": 0}
        )
        self.assertEqual(payload["summaries"][0]["node_id"], "local-node-a")
        self.assertEqual(
            payload["totals"],
            {
                "nodes": 2,
                "jobs": 4,
                "results": 4,
                "completed_jobs": 4,
                "failed_jobs": 0,
                "valid_results": 4,
                "invalid_results": 0,
                "unsupported_results": 0,
                "contribution_units": 4,
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

    def test_run_demo_default_output_shape_stays_single_result(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            exit_code = main(
                ["run-demo", "--node-id", "local-demo-node", "--message", "hello mesh"]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["node_id"], "local-demo-node")
        self.assertEqual(payload["output"], "hello mesh")
        self.assertNotIn("validation", payload)
        self.assertNotIn("ledger_summary", payload)

    def test_run_demo_persists_json_ledger_and_accumulates_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            first_stdout = io.StringIO()
            with contextlib.redirect_stdout(first_stdout):
                first_exit = main(
                    [
                        "run-demo",
                        "--node-id",
                        "local-demo-node",
                        "--message",
                        "hello mesh",
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            second_stdout = io.StringIO()
            with contextlib.redirect_stdout(second_stdout):
                second_exit = main(
                    [
                        "run-demo",
                        "--node-id",
                        "local-demo-node",
                        "--message",
                        "hello mesh",
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            persisted = json.loads(ledger_path.read_text(encoding="utf-8"))

        first_payload = json.loads(first_stdout.getvalue())
        second_payload = json.loads(second_stdout.getvalue())
        self.assertEqual(first_exit, 0)
        self.assertEqual(second_exit, 0)
        self.assertEqual(first_payload["result"]["output"], "hello mesh")
        self.assertEqual(first_payload["validation"]["valid"], True)
        self.assertEqual(first_payload["ledger_path"], str(ledger_path))
        self.assertEqual(
            first_payload["persisted_ledger_summary"]["total_result_count"], 1
        )
        self.assertEqual(
            second_payload["persisted_ledger_summary"]["total_result_count"], 2
        )
        self.assertEqual(
            second_payload["persisted_ledger_summary"]["total_contribution_units"], 2
        )
        self.assertEqual(len(persisted["records"]), 2)
        self.assertEqual(persisted["records"][0]["node_id"], "local-demo-node")
        self.assertEqual(persisted["records"][0]["contribution_units"], 1)

    def test_run_demo_malformed_ledger_path_returns_cli_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            ledger_path.write_text("not-json", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as cm:
                main(["run-demo", "--ledger-path", str(ledger_path)])

            self.assertEqual(cm.exception.code, 2)
            self.assertIn("ledger JSON is malformed", stderr.getvalue())
            self.assertEqual(ledger_path.read_text(encoding="utf-8"), "not-json")


if __name__ == "__main__":
    unittest.main()
