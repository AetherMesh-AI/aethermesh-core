import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.cli import main


class LocalTransportCliTests(unittest.TestCase):
    def test_materialize_local_inboxes_and_process_transport_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            dispatch_path = Path(temp_dir) / "dispatch.json"
            transport_dir = Path(temp_dir) / "transport"
            ledger_path = Path(temp_dir) / "ledger.json"
            state_path = Path(temp_dir) / "node-a-state.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a", "local-node-b"],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "one"},
                            },
                            {
                                "job_id": "echo-2",
                                "job_type": "echo",
                                "payload": {"message": "two"},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "dispatch-local-batch",
                            "--manifest",
                            str(manifest_path),
                            "--message-log-path",
                            str(dispatch_path),
                        ]
                    ),
                    0,
                )

            materialize_stdout = io.StringIO()
            with contextlib.redirect_stdout(materialize_stdout):
                materialize_exit = main(
                    [
                        "materialize-local-inboxes",
                        "--message-log-path",
                        str(dispatch_path),
                        "--transport-dir",
                        str(transport_dir),
                    ]
                )

            process_stdout = io.StringIO()
            with contextlib.redirect_stdout(process_stdout):
                process_exit = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--transport-dir",
                        str(transport_dir),
                        "--ledger-path",
                        str(ledger_path),
                        "--node-state-path",
                        str(state_path),
                    ]
                )
            rerun_stdout = io.StringIO()
            with contextlib.redirect_stdout(rerun_stdout):
                rerun_exit = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--transport-dir",
                        str(transport_dir),
                        "--ledger-path",
                        str(ledger_path),
                        "--node-state-path",
                        str(state_path),
                    ]
                )

            materialized = json.loads(materialize_stdout.getvalue())
            processed = json.loads(process_stdout.getvalue())
            rerun = json.loads(rerun_stdout.getvalue())
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            node_a_inbox = json.loads(
                (transport_dir / "inboxes" / "local-node-a.json").read_text(
                    encoding="utf-8"
                )
            )
            node_b_inbox = json.loads(
                (transport_dir / "inboxes" / "local-node-b.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(materialize_exit, 0)
        self.assertEqual(process_exit, 0)
        self.assertEqual(rerun_exit, 0)
        self.assertEqual(materialized["node_ids"], ["local-node-a", "local-node-b"])
        self.assertEqual(node_a_inbox["version"], 1)
        self.assertEqual(node_a_inbox["node_id"], "local-node-a")
        self.assertEqual(
            [message["recipient_node_id"] for message in node_a_inbox["messages"]],
            ["local-node-a"],
        )
        self.assertEqual(
            [message["recipient_node_id"] for message in node_b_inbox["messages"]],
            ["local-node-b"],
        )
        self.assertEqual(processed["processed_assignment_count"], 1)
        self.assertEqual(processed["validation_outcomes"][0]["valid"], True)
        self.assertEqual(processed["ledger_summary"]["total_units"], 1)
        self.assertEqual(rerun["processed_assignment_count"], 0)
        self.assertEqual(rerun["skipped_processed_message_ids"], ["msg-0003"])
        self.assertEqual(len(ledger["records"]), 1)
        self.assertEqual(ledger["records"][0]["node_id"], "local-node-a")

    def test_transport_inbox_failure_does_not_overwrite_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transport_dir = Path(temp_dir) / "transport"
            inbox_path = transport_dir / "inboxes" / "local-node-a.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            state_path = Path(temp_dir) / "state.json"
            output_path = Path(temp_dir) / "output.json"
            inbox_path.parent.mkdir(parents=True)
            inbox_path.write_text("not-json", encoding="utf-8")
            ledger_original = json.dumps({"version": 1, "records": [], "keep": True})
            state_original = json.dumps(
                {
                    "version": 1,
                    "node_id": "local-node-a",
                    "processed_message_ids": [],
                    "processed_assignment_count": 0,
                }
            )
            output_original = json.dumps({"version": 1, "messages": [], "keep": True})
            ledger_path.write_text(ledger_original, encoding="utf-8")
            state_path.write_text(state_original, encoding="utf-8")
            output_path.write_text(output_original, encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--transport-dir",
                        str(transport_dir),
                        "--ledger-path",
                        str(ledger_path),
                        "--node-state-path",
                        str(state_path),
                        "--output-message-log-path",
                        str(output_path),
                    ]
                )
            ledger_contents = ledger_path.read_text(encoding="utf-8")
            state_contents = state_path.read_text(encoding="utf-8")
            output_contents = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("local transport inbox JSON is malformed", stderr.getvalue())
        self.assertEqual(ledger_contents, ledger_original)
        self.assertEqual(state_contents, state_original)
        self.assertEqual(output_contents, output_original)

    def test_run_local_transport_flow_happy_path_and_idempotent_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "flow"
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-local-transport-flow",
                        "--manifest",
                        "examples/local-batch.json",
                        "--output-dir",
                        str(output_dir),
                    ]
                )
            rerun_stdout = io.StringIO()
            with contextlib.redirect_stdout(rerun_stdout):
                rerun_exit = main(
                    [
                        "run-local-transport-flow",
                        "--manifest",
                        "examples/local-batch.json",
                        "--output-dir",
                        str(output_dir),
                    ]
                )
            audit_stdout = io.StringIO()
            with contextlib.redirect_stdout(audit_stdout):
                audit_exit = main(["audit-local-flow", "--output-dir", str(output_dir)])

            payload = json.loads(stdout.getvalue())
            rerun_payload = json.loads(rerun_stdout.getvalue())
            audit_payload = json.loads(audit_stdout.getvalue())
            node_a_inbox = json.loads(
                (output_dir / "transport" / "inboxes" / "local-node-a.json").read_text(
                    encoding="utf-8"
                )
            )
            node_c_inbox = json.loads(
                (output_dir / "transport" / "inboxes" / "local-node-c.json").read_text(
                    encoding="utf-8"
                )
            )
            worker_log = json.loads(
                (output_dir / "worker-message-logs" / "local-node-a.json").read_text(
                    encoding="utf-8"
                )
            )
            artifact_exists = {
                "dispatch": (output_dir / "dispatch-message-log.json").exists(),
                "flow": (output_dir / "flow-message-log.json").exists(),
                "ledger": (output_dir / "ledger.json").exists(),
                "receipts": (output_dir / "receipts.json").exists(),
                "node_state_a": (output_dir / "node-state" / "local-node-a.json").exists(),
                "worker_log_c": (
                    output_dir / "worker-message-logs" / "local-node-c.json"
                ).exists(),
            }

        self.assertEqual(exit_code, 0)
        self.assertEqual(rerun_exit, 0)
        self.assertEqual(audit_exit, 0)
        self.assertEqual(payload["command"], "run-local-transport-flow")
        self.assertEqual(payload["inbox_count"], 2)
        self.assertEqual(payload["offline_node_ids"], ["local-node-b"])
        self.assertEqual(payload["processed_nodes"], ["local-node-a", "local-node-c"])
        self.assertEqual(payload["processed_assignment_count"], 5)
        self.assertEqual(payload["receipt_count"], 5)
        self.assertEqual(rerun_payload["processed_assignment_count"], 0)
        self.assertEqual(rerun_payload["receipt_count"], 5)
        self.assertEqual(audit_payload["ok"], True)
        self.assertTrue(artifact_exists["dispatch"])
        self.assertTrue(artifact_exists["flow"])
        self.assertTrue(artifact_exists["ledger"])
        self.assertTrue(artifact_exists["receipts"])
        self.assertTrue(artifact_exists["node_state_a"])
        self.assertTrue(artifact_exists["worker_log_c"])
        self.assertEqual(node_a_inbox["node_id"], "local-node-a")
        self.assertEqual(node_c_inbox["node_id"], "local-node-c")
        self.assertTrue(
            all(
                message["recipient_node_id"] == "local-node-a"
                for message in node_a_inbox["messages"]
            )
        )
        self.assertEqual(
            worker_log["metadata"]["source_message_log_path"],
            str(output_dir / "transport" / "inboxes" / "local-node-a.json"),
        )

    def test_run_local_transport_flow_existing_malformed_ledger_fails_before_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "flow"
            output_dir.mkdir()
            ledger_path = output_dir / "ledger.json"
            flow_path = output_dir / "flow-message-log.json"
            ledger_path.write_text("not-json", encoding="utf-8")
            flow_original = json.dumps({"version": 1, "messages": [], "keep": True})
            flow_path.write_text(flow_original, encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "run-local-transport-flow",
                        "--manifest",
                        "examples/local-batch.json",
                        "--output-dir",
                        str(output_dir),
                    ]
                )
            flow_contents = flow_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ledger JSON is malformed", stderr.getvalue())
        self.assertEqual(flow_contents, flow_original)

    def test_process_local_inbox_requires_one_input_source(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(["process-local-inbox", "--node-id", "local-node-a"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("provide exactly one", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
