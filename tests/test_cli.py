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
        self.assertEqual(len(payload["messages"]), 14)
        self.assertEqual(payload["messages"][0]["message_id"], "msg-0001")
        self.assertEqual(payload["messages"][0]["message_type"], "node_heartbeat")
        self.assertEqual(payload["messages"][0]["correlation_id"], None)
        self.assertEqual(payload["messages"][0]["recipient_node_id"], None)
        self.assertEqual(
            payload["messages"][0]["payload"],
            {
                "node_id": "local-node-a",
                "status": "available",
                "heartbeat_sequence": 1,
                "heartbeat_count": 1,
            },
        )
        self.assertEqual(payload["messages"][1]["message_type"], "node_heartbeat")
        self.assertEqual(payload["messages"][2]["message_type"], "job_assigned")
        self.assertEqual(payload["messages"][2]["correlation_id"], "echo-1")
        self.assertEqual(payload["messages"][2]["recipient_node_id"], "local-node-a")
        self.assertEqual(payload["messages"][3]["message_type"], "job_result_reported")
        self.assertEqual(payload["messages"][4]["message_type"], "contribution_recorded")
        self.assertEqual(payload["validations"][0]["valid"], True)
        self.assertEqual(
            payload["validation_summary"], {"valid": 4, "invalid": 0, "unsupported": 0}
        )
        self.assertEqual(payload["summaries"][0]["node_id"], "local-node-a")
        self.assertEqual(
            payload["node_roster"],
            [
                {
                    "node_id": "local-node-a",
                    "status": "available",
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                    "assigned_jobs": 2,
                    "contribution_units": 2,
                },
                {
                    "node_id": "local-node-b",
                    "status": "available",
                    "heartbeat_sequence": 2,
                    "heartbeat_count": 1,
                    "assigned_jobs": 2,
                    "contribution_units": 2,
                },
            ],
        )
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

    def test_run_local_batch_prints_manifest_backed_simulation_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a", "local-node-b"],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "hello mesh"},
                            },
                            {
                                "job_id": "text-stats-1",
                                "job_type": "text_stats",
                                "payload": {"text": "hello mesh\nhello node"},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["run-local-batch", "--manifest", str(manifest_path)])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["nodes"], ["local-node-a", "local-node-b"])
        self.assertEqual(
            payload["assignments"],
            [
                {"job_id": "echo-1", "node_id": "local-node-a"},
                {"job_id": "text-stats-1", "node_id": "local-node-b"},
            ],
        )
        self.assertEqual(payload["results"][0]["output"], "hello mesh")
        self.assertEqual(payload["results"][1]["output"]["word_count"], 4)
        self.assertEqual(
            payload["validation_summary"], {"valid": 2, "invalid": 0, "unsupported": 0}
        )
        self.assertEqual(payload["totals"]["jobs"], 2)
        self.assertEqual(payload["totals"]["contribution_units"], 2)

    def test_run_local_batch_skips_offline_manifest_nodes_and_prints_roster(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": [
                            {"node_id": "local-node-a", "status": "available"},
                            {"node_id": "local-node-b", "status": "offline"},
                            "local-node-c",
                        ],
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
                            {
                                "job_id": "echo-3",
                                "job_type": "echo",
                                "payload": {"message": "three"},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["run-local-batch", "--manifest", str(manifest_path)])

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["nodes"], ["local-node-a", "local-node-b", "local-node-c"])
        self.assertEqual(
            payload["assignments"],
            [
                {"job_id": "echo-1", "node_id": "local-node-a"},
                {"job_id": "echo-2", "node_id": "local-node-c"},
                {"job_id": "echo-3", "node_id": "local-node-a"},
            ],
        )
        self.assertEqual(
            payload["node_roster"],
            [
                {
                    "node_id": "local-node-a",
                    "status": "available",
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                    "assigned_jobs": 2,
                    "contribution_units": 2,
                },
                {
                    "node_id": "local-node-b",
                    "status": "offline",
                    "heartbeat_sequence": 0,
                    "heartbeat_count": 0,
                    "assigned_jobs": 0,
                    "contribution_units": 0,
                },
                {
                    "node_id": "local-node-c",
                    "status": "available",
                    "heartbeat_sequence": 2,
                    "heartbeat_count": 1,
                    "assigned_jobs": 1,
                    "contribution_units": 1,
                },
            ],
        )

    def test_run_local_batch_all_offline_returns_nonzero_without_writing_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": [{"node_id": "local-node-a", "status": "offline"}],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "hello mesh"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            ledger_exists = ledger_path.exists()

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("no available nodes for local job assignment", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertFalse(ledger_exists)

    def test_run_local_batch_manifest_error_returns_nonzero_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            manifest_path.write_text("not-json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(["run-local-batch", "--manifest", str(manifest_path)])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("error: manifest JSON is malformed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_run_local_batch_unsupported_job_type_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
                        "jobs": [
                            {"job_id": "bad-1", "job_type": "unknown", "payload": {}}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(["run-local-batch", "--manifest", str(manifest_path)])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Unsupported job type: unknown", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_run_local_batch_does_not_write_ledger_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "hello mesh"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["run-local-batch", "--manifest", str(manifest_path)])
            payload = json.loads(stdout.getvalue())
            ledger_exists = ledger_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertFalse(ledger_exists)
        self.assertNotIn("ledger_path", payload)
        self.assertNotIn("persisted_ledger_summaries", payload)

    def test_run_local_batch_persists_json_ledger_and_accumulates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a", "local-node-b"],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "hello mesh"},
                            },
                            {
                                "job_id": "text-stats-1",
                                "job_type": "text_stats",
                                "payload": {"text": "hello mesh\nhello node"},
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            first_stdout = io.StringIO()
            with contextlib.redirect_stdout(first_stdout):
                first_exit = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            second_stdout = io.StringIO()
            with contextlib.redirect_stdout(second_stdout):
                second_exit = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            persisted = json.loads(ledger_path.read_text(encoding="utf-8"))

        first_payload = json.loads(first_stdout.getvalue())
        second_payload = json.loads(second_stdout.getvalue())
        self.assertEqual(first_exit, 0)
        self.assertEqual(second_exit, 0)
        self.assertEqual(first_payload["ledger_path"], str(ledger_path))
        self.assertEqual(len(first_payload["results"]), 2)
        self.assertEqual(
            first_payload["persisted_ledger_summaries"][0]["total_result_count"], 1
        )
        self.assertEqual(
            first_payload["persisted_ledger_summaries"][1]["total_contribution_units"], 1
        )
        self.assertEqual(
            second_payload["persisted_ledger_summaries"][0]["total_result_count"], 2
        )
        self.assertEqual(
            second_payload["persisted_ledger_summaries"][1]["total_contribution_units"], 2
        )
        self.assertEqual(persisted["version"], 1)
        self.assertEqual(len(persisted["records"]), 4)
        self.assertEqual(persisted["records"][0]["node_id"], "local-node-a")
        self.assertEqual(persisted["records"][0]["validation_valid"], True)
        self.assertEqual(persisted["records"][0]["validation_reason"], "ok")
        self.assertEqual(persisted["records"][0]["job_type"], "echo")
        self.assertEqual(persisted["records"][1]["node_id"], "local-node-b")
        self.assertEqual(persisted["records"][1]["validation_valid"], True)
        self.assertEqual(persisted["records"][1]["validation_reason"], "ok")
        self.assertEqual(persisted["records"][1]["job_type"], "text_stats")

    def test_run_local_batch_preserves_existing_ledger_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "hello mesh"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            ledger_path.write_text(
                json.dumps({"version": 1, "records": [], "owner": "local-dev"}),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            persisted = json.loads(ledger_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(persisted["owner"], "local-dev")
        self.assertEqual(len(persisted["records"]), 1)

    def test_run_local_batch_persists_invalid_completed_result_with_zero_units(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
                        "jobs": [
                            {"job_id": "echo-1", "job_type": "echo", "payload": {}}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            persisted = json.loads(ledger_path.read_text(encoding="utf-8"))

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["validation_summary"], {"valid": 0, "invalid": 1, "unsupported": 0})
        self.assertEqual(persisted["records"][0]["status"], "completed")
        self.assertEqual(persisted["records"][0]["contribution_units"], 0)
        self.assertEqual(persisted["records"][0]["validation_valid"], False)
        self.assertEqual(
            persisted["records"][0]["validation_reason"], "missing_payload_message"
        )
        self.assertEqual(persisted["records"][0]["job_type"], "echo")

    def test_run_local_batch_unsupported_job_type_persists_invalid_audit_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
                        "jobs": [
                            {"job_id": "bad-1", "job_type": "unknown", "payload": {}}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            persisted = json.loads(ledger_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("Unsupported job type: unknown", stderr.getvalue())
        self.assertEqual(len(persisted["records"]), 1)
        self.assertEqual(persisted["records"][0]["status"], "failed")
        self.assertEqual(persisted["records"][0]["contribution_units"], 0)
        self.assertEqual(persisted["records"][0]["validation_valid"], False)
        self.assertEqual(persisted["records"][0]["validation_reason"], "unsupported_job_type")
        self.assertEqual(persisted["records"][0]["job_type"], "unknown")

    def test_run_local_batch_malformed_ledger_returns_nonzero_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "hello mesh"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            ledger_path.write_text("not-json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            ledger_contents = ledger_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ledger JSON is malformed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(ledger_contents, "not-json")

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

    def test_run_demo_identity_path_creates_and_reuses_node_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            first_stdout = io.StringIO()
            with contextlib.redirect_stdout(first_stdout):
                first_exit = main(
                    [
                        "run-demo",
                        "--identity-path",
                        str(identity_path),
                        "--message",
                        "hello mesh",
                    ]
                )
            second_stdout = io.StringIO()
            with contextlib.redirect_stdout(second_stdout):
                second_exit = main(
                    [
                        "run-demo",
                        "--identity-path",
                        str(identity_path),
                        "--message",
                        "hello again",
                    ]
                )
            persisted = json.loads(identity_path.read_text(encoding="utf-8"))

        first_payload = json.loads(first_stdout.getvalue())
        second_payload = json.loads(second_stdout.getvalue())
        self.assertEqual(first_exit, 0)
        self.assertEqual(second_exit, 0)
        self.assertTrue(first_payload["node_id"].startswith("local-"))
        self.assertEqual(second_payload["node_id"], first_payload["node_id"])
        self.assertEqual(persisted["version"], 1)
        self.assertEqual(persisted["node"]["node_id"], first_payload["node_id"])
        self.assertNotIn("validation", first_payload)
        self.assertNotIn("ledger_summary", first_payload)

    def test_run_demo_node_id_and_identity_path_conflict_returns_cli_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as cm:
                main(
                    [
                        "run-demo",
                        "--node-id",
                        "local-demo-node",
                        "--identity-path",
                        str(identity_path),
                    ]
                )

            self.assertFalse(identity_path.exists())

        self.assertEqual(cm.exception.code, 2)
        self.assertIn("mutually exclusive", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_run_demo_malformed_identity_path_returns_cli_error_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            identity_path.write_text("not-json", encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as cm:
                main(["run-demo", "--identity-path", str(identity_path)])

            identity_contents = identity_path.read_text(encoding="utf-8")

        self.assertEqual(cm.exception.code, 2)
        self.assertIn("identity JSON is malformed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(identity_contents, "not-json")

    def test_run_demo_unsupported_identity_version_returns_cli_error_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            original = json.dumps({"version": 2, "node": {"node_id": "local-future"}})
            identity_path.write_text(original, encoding="utf-8")
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as cm:
                main(["run-demo", "--identity-path", str(identity_path)])

            identity_contents = identity_path.read_text(encoding="utf-8")

        self.assertEqual(cm.exception.code, 2)
        self.assertIn("identity JSON must contain version 1", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(identity_contents, original)

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
        self.assertEqual(persisted["records"][0]["validation_valid"], True)
        self.assertEqual(persisted["records"][0]["validation_reason"], "ok")
        self.assertEqual(persisted["records"][0]["job_type"], "echo")

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

    def test_ledger_summary_prints_deterministic_json_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            original = json.dumps(
                {
                    "version": 1,
                    "records": [
                        {
                            "node_id": "node-b",
                            "job_id": "job-1",
                            "status": "completed",
                            "contribution_units": 10,
                            "message": "ok",
                        },
                        {
                            "node_id": "node-a",
                            "job_id": "job-2",
                            "status": "failed",
                            "contribution_units": 0,
                            "message": "boom",
                        },
                        {
                            "node_id": "node-a",
                            "job_id": "job-3",
                            "status": "completed",
                            "contribution_units": 5,
                            "message": "ok",
                        },
                    ],
                    "owner": "local-dev",
                },
                sort_keys=True,
            )
            ledger_path.write_text(original, encoding="utf-8")
            before_mtime = ledger_path.stat().st_mtime_ns
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(["ledger-summary", "--ledger-path", str(ledger_path)])

            after_mtime = ledger_path.stat().st_mtime_ns
            after_contents = ledger_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(after_mtime, before_mtime)
        self.assertEqual(after_contents, original)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            {
                "ledger_path": str(ledger_path),
                "record_count": 3,
                "completed_result_count": 2,
                "failed_result_count": 1,
                "total_contribution_units": 15,
                "nodes": [
                    {
                        "node_id": "node-a",
                        "record_count": 2,
                        "completed_result_count": 1,
                        "failed_result_count": 1,
                        "total_contribution_units": 5,
                    },
                    {
                        "node_id": "node-b",
                        "record_count": 1,
                        "completed_result_count": 1,
                        "failed_result_count": 0,
                        "total_contribution_units": 10,
                    },
                ],
            },
        )

    def test_ledger_summary_missing_file_returns_nonzero_without_creating_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "missing" / "ledger.json"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(["ledger-summary", "--ledger-path", str(ledger_path)])

            ledger_exists = ledger_path.exists()
            parent_exists = ledger_path.parent.exists()

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ledger file does not exist", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertFalse(ledger_exists)
        self.assertFalse(parent_exists)

    def test_ledger_summary_malformed_ledger_returns_nonzero_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            ledger_path.write_text("not-json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(["ledger-summary", "--ledger-path", str(ledger_path)])

            contents = ledger_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ledger JSON is malformed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(contents, "not-json")

    def test_ledger_summary_non_object_ledger_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            ledger_path.write_text("[]", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(["ledger-summary", "--ledger-path", str(ledger_path)])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ledger JSON must be an object", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_ledger_summary_unsupported_version_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            original = json.dumps({"version": 2, "records": []})
            ledger_path.write_text(original, encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(["ledger-summary", "--ledger-path", str(ledger_path)])

            contents = ledger_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ledger JSON must contain version 1", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(contents, original)

    def test_ledger_summary_invalid_record_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.json"
            original = json.dumps(
                {"version": 1, "records": [{"node_id": "node-a"}]}, sort_keys=True
            )
            ledger_path.write_text(original, encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(["ledger-summary", "--ledger-path", str(ledger_path)])

            contents = ledger_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("ledger record field 'job_id' must be str", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(contents, original)


if __name__ == "__main__":
    unittest.main()
