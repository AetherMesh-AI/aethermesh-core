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
            output_path = Path(temp_dir) / "node-a-worker-log.json"
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
                        "--output-message-log-path",
                        str(output_path),
                        "--write-transport-outbox",
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
            outbox = json.loads(
                (transport_dir / "outboxes" / "local-node-a.json").read_text(
                    encoding="utf-8"
                )
            )
            worker_log = json.loads(output_path.read_text(encoding="utf-8"))
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
        self.assertEqual(
            processed["transport_outbox_path"],
            str(transport_dir / "outboxes" / "local-node-a.json"),
        )
        self.assertEqual(processed["transport_outbox_message_count"], 1)
        self.assertEqual(processed["output_message_log_path"], str(output_path))
        self.assertEqual(outbox["version"], 1)
        self.assertEqual(outbox["node_id"], "local-node-a")
        self.assertEqual(
            [message["sender_node_id"] for message in outbox["messages"]],
            ["local-node-a"],
        )
        self.assertEqual(
            [message["message_id"] for message in outbox["messages"]],
            [
                message["message_id"]
                for message in worker_log["messages"]
                if message["sender_node_id"] == "local-node-a"
            ],
        )
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
            outbox_path = transport_dir / "outboxes" / "local-node-a.json"
            inbox_path.parent.mkdir(parents=True)
            outbox_path.parent.mkdir(parents=True)
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
            outbox_original = json.dumps(
                {"version": 1, "node_id": "local-node-a", "messages": [], "keep": True}
            )
            ledger_path.write_text(ledger_original, encoding="utf-8")
            state_path.write_text(state_original, encoding="utf-8")
            output_path.write_text(output_original, encoding="utf-8")
            outbox_path.write_text(outbox_original, encoding="utf-8")
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
                        "--write-transport-outbox",
                    ]
                )
            ledger_contents = ledger_path.read_text(encoding="utf-8")
            state_contents = state_path.read_text(encoding="utf-8")
            output_contents = output_path.read_text(encoding="utf-8")
            outbox_contents = outbox_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("local transport inbox JSON is malformed", stderr.getvalue())
        self.assertEqual(ledger_contents, ledger_original)
        self.assertEqual(state_contents, state_original)
        self.assertEqual(output_contents, output_original)
        self.assertEqual(outbox_contents, outbox_original)

    def test_process_local_inbox_rejects_transport_outbox_without_transport_dir(
        self,
    ) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(
                [
                    "process-local-inbox",
                    "--node-id",
                    "local-node-a",
                    "--message-log-path",
                    "unused.json",
                    "--write-transport-outbox",
                ]
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn(
            "--write-transport-outbox requires --transport-dir", stderr.getvalue()
        )

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
