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
                {"job_id": "text-stats-1", "node_id": "local-node-a"},
                {"job_id": "echo-2", "node_id": "local-node-b"},
                {"job_id": "echo-3", "node_id": "local-node-a"},
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
                    "capabilities": ["echo", "text_stats"],
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                    "assigned_jobs": 3,
                    "contribution_units": 3,
                },
                {
                    "node_id": "local-node-b",
                    "status": "available",
                    "capabilities": ["echo", "text_stats"],
                    "heartbeat_sequence": 2,
                    "heartbeat_count": 1,
                    "assigned_jobs": 1,
                    "contribution_units": 1,
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
                {"job_id": "text-stats-1", "node_id": "local-node-a"},
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
                    "capabilities": ["echo", "text_stats"],
                    "heartbeat_sequence": 1,
                    "heartbeat_count": 1,
                    "assigned_jobs": 2,
                    "contribution_units": 2,
                },
                {
                    "node_id": "local-node-b",
                    "status": "offline",
                    "capabilities": ["echo", "text_stats"],
                    "heartbeat_sequence": 0,
                    "heartbeat_count": 0,
                    "assigned_jobs": 0,
                    "contribution_units": 0,
                },
                {
                    "node_id": "local-node-c",
                    "status": "available",
                    "capabilities": ["echo", "text_stats"],
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

    def test_run_local_batch_no_capable_node_returns_nonzero(self) -> None:
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
        self.assertIn("job_id=bad-1 job_type=unknown", stderr.getvalue())
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

    def test_run_local_batch_does_not_write_message_log_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            message_log_path = Path(temp_dir) / "local-messages.json"
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
            message_log_exists = message_log_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertFalse(message_log_exists)
        self.assertNotIn("message_log_path", payload)

    def test_run_local_batch_writes_message_log_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            message_log_path = Path(temp_dir) / "nested" / "local-messages.json"
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
                exit_code = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )
            payload = json.loads(stdout.getvalue())
            persisted = json.loads(message_log_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["message_log_path"], str(message_log_path))
        self.assertEqual(persisted["version"], 1)
        self.assertEqual(persisted["metadata"]["manifest_path"], str(manifest_path))
        self.assertEqual(persisted["metadata"]["message_count"], 8)
        self.assertEqual(persisted["metadata"]["job_count"], 2)
        self.assertEqual(persisted["metadata"]["completed_count"], 2)
        self.assertEqual(persisted["metadata"]["failed_count"], 0)
        self.assertEqual(persisted["metadata"]["total_contribution_units"], 2)
        self.assertEqual(
            [message["message_id"] for message in persisted["messages"]],
            [f"msg-{index:04d}" for index in range(1, 9)],
        )
        self.assertEqual(persisted["messages"][0]["message_type"], "node_heartbeat")
        self.assertEqual(persisted["messages"][2]["message_type"], "job_assigned")
        self.assertEqual(persisted["messages"][3]["message_type"], "job_result_reported")
        self.assertEqual(persisted["messages"][4]["message_type"], "contribution_recorded")

    def test_run_local_batch_message_log_write_error_returns_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            message_log_path = Path(temp_dir) / "local-messages.json"
            message_log_path.mkdir()
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
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "run-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("could not write message log file", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

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
            first_payload["persisted_ledger_summaries"][0]["total_result_count"], 2
        )
        self.assertEqual(
            first_payload["persisted_ledger_summaries"][1]["total_contribution_units"], 0
        )
        self.assertEqual(
            second_payload["persisted_ledger_summaries"][0]["total_result_count"], 4
        )
        self.assertEqual(
            second_payload["persisted_ledger_summaries"][1]["total_contribution_units"], 0
        )
        self.assertEqual(persisted["version"], 1)
        self.assertEqual(len(persisted["records"]), 4)
        self.assertEqual(persisted["records"][0]["node_id"], "local-node-a")
        self.assertEqual(persisted["records"][0]["validation_valid"], True)
        self.assertEqual(persisted["records"][0]["validation_reason"], "ok")
        self.assertEqual(persisted["records"][0]["job_type"], "echo")
        self.assertEqual(persisted["records"][1]["node_id"], "local-node-a")
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
                        "nodes": [
                            {
                                "node_id": "local-node-a",
                                "capabilities": ["unknown"],
                            }
                        ],
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

    def test_dispatch_local_batch_writes_assignment_only_message_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            message_log_path = Path(temp_dir) / "local-dispatch.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": [
                            {"node_id": "local-node-a", "capabilities": ["echo", "text_stats"]},
                            {"node_id": "local-node-b", "status": "offline", "capabilities": ["echo"]},
                            {"node_id": "local-node-c", "capabilities": ["echo"]},
                        ],
                        "jobs": [
                            {"job_id": "echo-1", "job_type": "echo", "payload": {"message": "one"}},
                            {"job_id": "stats-1", "job_type": "text_stats", "payload": {"text": "hello mesh"}},
                            {"job_id": "echo-2", "job_type": "echo", "payload": {"message": "two"}},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "dispatch-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )
            payload = json.loads(stdout.getvalue())
            persisted = json.loads(message_log_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertFalse(ledger_path.exists())
        self.assertEqual(payload["command"], "dispatch-local-batch")
        self.assertEqual(payload["manifest_path"], str(manifest_path))
        self.assertEqual(payload["message_log_path"], str(message_log_path))
        self.assertEqual(payload["job_count"], 3)
        self.assertEqual(payload["assignment_count"], 3)
        self.assertEqual(payload["message_count"], 5)
        self.assertEqual(payload["assigned_node_ids"], ["local-node-a", "local-node-c"])
        self.assertEqual(
            payload["assignments"],
            [
                {"job_id": "echo-1", "node_id": "local-node-a"},
                {"job_id": "stats-1", "node_id": "local-node-a"},
                {"job_id": "echo-2", "node_id": "local-node-c"},
            ],
        )
        self.assertEqual(payload["nodes"][1]["status"], "offline")
        self.assertEqual(persisted["version"], 1)
        self.assertEqual(persisted["metadata"]["source"], "dispatch-local-batch")
        self.assertEqual(persisted["metadata"]["assignment_count"], 3)
        self.assertEqual(
            [message["message_type"] for message in persisted["messages"]],
            ["node_heartbeat", "node_heartbeat", "job_assigned", "job_assigned", "job_assigned"],
        )
        self.assertEqual(
            [message["sender_node_id"] for message in persisted["messages"][:2]],
            ["local-node-a", "local-node-c"],
        )
        self.assertNotIn("job_result_reported", json.dumps(persisted))
        self.assertNotIn("contribution_recorded", json.dumps(persisted))

    def test_dispatch_local_batch_failure_does_not_overwrite_existing_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            message_log_path = Path(temp_dir) / "local-dispatch.json"
            original = json.dumps({"version": 1, "messages": [], "keep": True})
            message_log_path.write_text(original, encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": [{"node_id": "local-node-a", "capabilities": ["echo"]}],
                        "jobs": [{"job_id": "stats-1", "job_type": "text_stats", "payload": {}}],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "dispatch-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )
            contents = message_log_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("job_id=stats-1 job_type=text_stats", stderr.getvalue())
        self.assertEqual(contents, original)

    def test_dispatch_local_batch_malformed_manifest_does_not_create_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            message_log_path = Path(temp_dir) / "local-dispatch.json"
            manifest_path.write_text("not-json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "dispatch-local-batch",
                        "--manifest",
                        str(manifest_path),
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("manifest JSON is malformed", stderr.getvalue())
        self.assertFalse(message_log_path.exists())

    def test_process_local_inbox_consumes_dispatch_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            message_log_path = Path(temp_dir) / "local-dispatch.json"
            ledger_path = Path(temp_dir) / "local-ledger.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
                        "jobs": [
                            {"job_id": "echo-1", "job_type": "echo", "payload": {"message": "hello mesh"}}
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
                            str(message_log_path),
                        ]
                    ),
                    0,
                )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--message-log-path",
                        str(message_log_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )
            payload = json.loads(stdout.getvalue())
            persisted_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["processed_assignment_count"], 1)
        self.assertEqual(payload["validation_outcomes"][0]["valid"], True)
        self.assertEqual(payload["ledger_summary"]["total_units"], 1)
        self.assertEqual(len(persisted_ledger["records"]), 1)
        self.assertEqual(persisted_ledger["records"][0]["job_id"], "echo-1")

    def test_process_local_inbox_replays_message_log_for_requested_node(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            message_log_path = Path(temp_dir) / "local-messages.json"
            ledger_path = Path(temp_dir) / "local-ledger.json"
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
                            {
                                "job_id": "text-stats-1",
                                "job_type": "text_stats",
                                "payload": {"text": "hello mesh"},
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
                            "run-local-batch",
                            "--manifest",
                            str(manifest_path),
                            "--message-log-path",
                            str(message_log_path),
                        ]
                    ),
                    0,
                )
            before_message_log = message_log_path.read_text(encoding="utf-8")
            before_mtime = message_log_path.stat().st_mtime_ns
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--message-log-path",
                        str(message_log_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )

            after_message_log = message_log_path.read_text(encoding="utf-8")
            after_mtime = message_log_path.stat().st_mtime_ns
            persisted_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["command"], "process-local-inbox")
        self.assertEqual(payload["node_id"], "local-node-a")
        self.assertEqual(payload["processed_assignment_count"], 2)
        self.assertEqual(payload["ignored_message_ids"], ["msg-0005", "msg-0011"])
        self.assertEqual(
            payload["emitted_messages"],
            [
                {
                    "id": "msg-0012",
                    "type": "job_result_reported",
                    "sender": "local-node-a",
                    "recipient": "local-ledger",
                },
                {
                    "id": "msg-0013",
                    "type": "contribution_recorded",
                    "sender": "local-ledger",
                    "recipient": "local-node-a",
                },
                {
                    "id": "msg-0014",
                    "type": "job_result_reported",
                    "sender": "local-node-a",
                    "recipient": "local-ledger",
                },
                {
                    "id": "msg-0015",
                    "type": "contribution_recorded",
                    "sender": "local-ledger",
                    "recipient": "local-node-a",
                },
            ],
        )
        self.assertEqual(
            payload["validation_outcomes"],
            [
                {"job_id": "echo-1", "valid": True, "credited_units": 1, "reason": "ok"},
                {
                    "job_id": "text-stats-1",
                    "valid": True,
                    "credited_units": 1,
                    "reason": "ok",
                },
            ],
        )
        self.assertEqual(
            payload["ledger_summary"],
            {
                "path": str(ledger_path),
                "total_units": 2,
                "node_units": 2,
                "record_count": 2,
            },
        )
        self.assertEqual(len(persisted_ledger["records"]), 2)
        self.assertEqual([record["node_id"] for record in persisted_ledger["records"]], ["local-node-a", "local-node-a"])
        self.assertEqual(after_message_log, before_message_log)
        self.assertEqual(after_mtime, before_mtime)
        self.assertNotIn("output_message_log_path", payload)
        self.assertNotIn("final_message_count", payload)

    def test_process_local_inbox_writes_output_message_log_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-messages.json"
            output_message_log_path = Path(temp_dir) / "local-node-a-output-messages.json"
            ledger_path = Path(temp_dir) / "local-ledger.json"
            message_log_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "metadata": {"message_count": 3},
                        "messages": [
                            {
                                "message_id": "msg-0001",
                                "message_type": "node_heartbeat",
                                "sender_node_id": "local-node-a",
                                "recipient_node_id": None,
                                "payload": {"node_id": "local-node-a"},
                                "correlation_id": None,
                            },
                            {
                                "message_id": "msg-0002",
                                "message_type": "job_assigned",
                                "sender_node_id": "local-scheduler",
                                "recipient_node_id": "local-node-a",
                                "payload": {
                                    "job_id": "echo-1",
                                    "job_type": "echo",
                                    "payload": {"message": "hello mesh"},
                                },
                                "correlation_id": "echo-1",
                            },
                            {
                                "message_id": "msg-0003",
                                "message_type": "contribution_recorded",
                                "sender_node_id": "local-ledger",
                                "recipient_node_id": "local-node-a",
                                "payload": {"job_id": "older-job", "contribution_units": 1},
                                "correlation_id": "older-job",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--message-log-path",
                        str(message_log_path),
                        "--ledger-path",
                        str(ledger_path),
                        "--output-message-log-path",
                        str(output_message_log_path),
                    ]
                )
            persisted = json.loads(output_message_log_path.read_text(encoding="utf-8"))

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["output_message_log_path"], str(output_message_log_path))
        self.assertEqual(payload["final_message_count"], 5)
        self.assertEqual(payload["processed_assignment_count"], 1)
        self.assertEqual(payload["ignored_message_ids"], ["msg-0003"])
        self.assertEqual(persisted["version"], 1)
        self.assertEqual(persisted["metadata"]["source"], "process-local-inbox")
        self.assertEqual(persisted["metadata"]["node_id"], "local-node-a")
        self.assertEqual(persisted["metadata"]["source_message_log_path"], str(message_log_path))
        self.assertEqual(persisted["metadata"]["ledger_path"], str(ledger_path))
        self.assertEqual(persisted["metadata"]["message_count"], 5)
        self.assertEqual(persisted["metadata"]["replayed_message_count"], 3)
        self.assertEqual(persisted["metadata"]["emitted_message_count"], 2)
        self.assertEqual(
            [message["message_id"] for message in persisted["messages"]],
            ["msg-0001", "msg-0002", "msg-0003", "msg-0004", "msg-0005"],
        )
        self.assertEqual(persisted["messages"][3]["message_type"], "job_result_reported")
        self.assertEqual(persisted["messages"][4]["message_type"], "contribution_recorded")

    def test_process_local_inbox_output_message_log_ordering_is_deterministic(self) -> None:
        document = {
            "version": 1,
            "messages": [
                {
                    "message_id": "msg-0001",
                    "message_type": "job_assigned",
                    "sender_node_id": "local-scheduler",
                    "recipient_node_id": "local-node-a",
                    "payload": {
                        "job_id": "echo-1",
                        "job_type": "echo",
                        "payload": {"message": "one"},
                    },
                    "correlation_id": "echo-1",
                },
                {
                    "message_id": "msg-0002",
                    "message_type": "job_assigned",
                    "sender_node_id": "local-scheduler",
                    "recipient_node_id": "local-node-a",
                    "payload": {
                        "job_id": "echo-2",
                        "job_type": "echo",
                        "payload": {"message": "two"},
                    },
                    "correlation_id": "echo-2",
                },
            ],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-messages.json"
            first_output_path = Path(temp_dir) / "first-output.json"
            second_output_path = Path(temp_dir) / "second-output.json"
            message_log_path.write_text(json.dumps(document), encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "process-local-inbox",
                            "--node-id",
                            "local-node-a",
                            "--message-log-path",
                            str(message_log_path),
                            "--output-message-log-path",
                            str(first_output_path),
                        ]
                    ),
                    0,
                )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    main(
                        [
                            "process-local-inbox",
                            "--node-id",
                            "local-node-a",
                            "--message-log-path",
                            str(message_log_path),
                            "--output-message-log-path",
                            str(second_output_path),
                        ]
                    ),
                    0,
                )
            first = json.loads(first_output_path.read_text(encoding="utf-8"))
            second = json.loads(second_output_path.read_text(encoding="utf-8"))

        self.assertEqual(first["messages"], second["messages"])
        self.assertEqual(
            [message["message_id"] for message in first["messages"]],
            ["msg-0001", "msg-0002", "msg-0003", "msg-0004", "msg-0005", "msg-0006"],
        )

    def test_process_local_inbox_unknown_node_returns_zero_without_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-messages.json"
            ledger_path = Path(temp_dir) / "local-ledger.json"
            message_log_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            {
                                "message_id": "msg-0001",
                                "message_type": "node_heartbeat",
                                "sender_node_id": "local-node-a",
                                "recipient_node_id": None,
                                "payload": {"node_id": "local-node-a"},
                                "correlation_id": None,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "unknown-node",
                        "--message-log-path",
                        str(message_log_path),
                    ]
                )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["processed_assignment_count"], 0)
        self.assertEqual(payload["ignored_message_ids"], [])
        self.assertEqual(payload["emitted_messages"], [])
        self.assertEqual(payload["validation_outcomes"], [])
        self.assertFalse(ledger_path.exists())
        self.assertNotIn("ledger_summary", payload)

    def test_process_local_inbox_invalid_node_state_returns_nonzero_without_writes(self) -> None:
        cases = [
            ("malformed", "not-json", "node state JSON is malformed"),
            (
                "wrong-node",
                json.dumps(
                    {
                        "version": 1,
                        "node_id": "other-node",
                        "processed_message_ids": [],
                        "processed_assignment_count": 0,
                    }
                ),
                "belongs to node 'other-node'",
            ),
            (
                "unsupported-version",
                json.dumps(
                    {
                        "version": 2,
                        "node_id": "local-node-a",
                        "processed_message_ids": [],
                        "processed_assignment_count": 0,
                    }
                ),
                "must contain version 1",
            ),
        ]
        for name, state_contents, expected_error in cases:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as temp_dir:
                    message_log_path = Path(temp_dir) / "local-messages.json"
                    ledger_path = Path(temp_dir) / "local-ledger.json"
                    output_message_log_path = Path(temp_dir) / "output-messages.json"
                    state_path = Path(temp_dir) / "node-state.json"
                    message_log_path.write_text(
                        json.dumps(
                            {
                                "version": 1,
                                "messages": [
                                    {
                                        "message_id": "msg-0001",
                                        "message_type": "job_assigned",
                                        "sender_node_id": "local-scheduler",
                                        "recipient_node_id": "local-node-a",
                                        "payload": {
                                            "job_id": "echo-1",
                                            "job_type": "echo",
                                            "payload": {"message": "hello mesh"},
                                        },
                                        "correlation_id": "echo-1",
                                    }
                                ],
                            }
                        ),
                        encoding="utf-8",
                    )
                    output_message_log_path.write_text("keep output", encoding="utf-8")
                    state_path.write_text(state_contents, encoding="utf-8")
                    original_state = state_path.read_text(encoding="utf-8")
                    stdout = io.StringIO()
                    stderr = io.StringIO()

                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        exit_code = main(
                            [
                                "process-local-inbox",
                                "--node-id",
                                "local-node-a",
                                "--message-log-path",
                                str(message_log_path),
                                "--ledger-path",
                                str(ledger_path),
                                "--output-message-log-path",
                                str(output_message_log_path),
                                "--node-state-path",
                                str(state_path),
                            ]
                        )

                    self.assertEqual(exit_code, 1)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn(expected_error, stderr.getvalue())
                    self.assertFalse(ledger_path.exists())
                    self.assertEqual(output_message_log_path.read_text(encoding="utf-8"), "keep output")
                    self.assertEqual(state_path.read_text(encoding="utf-8"), original_state)

    def test_process_local_inbox_with_node_state_resumes_without_duplicate_ledger_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-messages.json"
            ledger_path = Path(temp_dir) / "local-ledger.json"
            state_path = Path(temp_dir) / "node-state.json"
            message_log_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            {
                                "message_id": "msg-0001",
                                "message_type": "job_assigned",
                                "sender_node_id": "local-scheduler",
                                "recipient_node_id": "local-node-a",
                                "payload": {
                                    "job_id": "echo-1",
                                    "job_type": "echo",
                                    "payload": {"message": "hello mesh"},
                                },
                                "correlation_id": "echo-1",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            first_stdout = io.StringIO()
            with contextlib.redirect_stdout(first_stdout):
                first_exit = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--message-log-path",
                        str(message_log_path),
                        "--ledger-path",
                        str(ledger_path),
                        "--node-state-path",
                        str(state_path),
                    ]
                )
            first_payload = json.loads(first_stdout.getvalue())
            first_state = json.loads(state_path.read_text(encoding="utf-8"))

            second_stdout = io.StringIO()
            with contextlib.redirect_stdout(second_stdout):
                second_exit = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--message-log-path",
                        str(message_log_path),
                        "--ledger-path",
                        str(ledger_path),
                        "--node-state-path",
                        str(state_path),
                    ]
                )
            second_payload = json.loads(second_stdout.getvalue())
            second_state = json.loads(state_path.read_text(encoding="utf-8"))
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

        self.assertEqual(first_exit, 0)
        self.assertEqual(first_payload["processed_assignment_count"], 1)
        self.assertEqual(first_payload["skipped_processed_message_ids"], [])
        self.assertEqual(first_state["node_id"], "local-node-a")
        self.assertEqual(first_state["processed_message_ids"], ["msg-0001"])
        self.assertEqual(first_state["processed_assignment_count"], 1)
        self.assertEqual(second_exit, 0)
        self.assertEqual(second_payload["processed_assignment_count"], 0)
        self.assertEqual(second_payload["ignored_message_ids"], ["msg-0001"])
        self.assertEqual(second_payload["skipped_processed_message_ids"], ["msg-0001"])
        self.assertEqual(second_payload["processed_message_ids"], ["msg-0001"])
        self.assertEqual(second_state, first_state)
        self.assertEqual(len(ledger["records"]), 1)

    def test_process_local_inbox_invalid_message_log_does_not_write_output_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-messages.json"
            output_message_log_path = Path(temp_dir) / "output-messages.json"
            output_message_log_path.write_text("keep me", encoding="utf-8")
            message_log_path.write_text("not-json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--message-log-path",
                        str(message_log_path),
                        "--output-message-log-path",
                        str(output_message_log_path),
                    ]
                )
            output_contents = output_message_log_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("message log JSON is malformed", stderr.getvalue())
        self.assertEqual(output_contents, "keep me")

    def test_process_local_inbox_invalid_message_log_returns_nonzero_without_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "local-messages.json"
            ledger_path = Path(temp_dir) / "local-ledger.json"
            message_log_path.write_text("not-json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "process-local-inbox",
                        "--node-id",
                        "local-node-a",
                        "--message-log-path",
                        str(message_log_path),
                        "--ledger-path",
                        str(ledger_path),
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("message log JSON is malformed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertFalse(ledger_path.exists())

    def test_collect_local_results_end_to_end_from_dispatch_and_worker_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            dispatch_path = Path(temp_dir) / "local-dispatch.json"
            worker_a_path = Path(temp_dir) / "local-node-a-output.json"
            worker_b_path = Path(temp_dir) / "local-node-b-output.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": [
                            "local-node-a",
                            {"node_id": "local-node-b", "status": "offline"},
                        ],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "one"},
                            }
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
                self.assertEqual(
                    main(
                        [
                            "process-local-inbox",
                            "--node-id",
                            "local-node-a",
                            "--message-log-path",
                            str(dispatch_path),
                            "--output-message-log-path",
                            str(worker_a_path),
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    main(
                        [
                            "process-local-inbox",
                            "--node-id",
                            "local-node-b",
                            "--message-log-path",
                            str(dispatch_path),
                            "--output-message-log-path",
                            str(worker_b_path),
                        ]
                    ),
                    0,
                )
            before_dispatch = dispatch_path.read_text(encoding="utf-8")
            before_worker_a = worker_a_path.read_text(encoding="utf-8")
            before_worker_b = worker_b_path.read_text(encoding="utf-8")
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "collect-local-results",
                        "--dispatch-message-log-path",
                        str(dispatch_path),
                        "--worker-message-log-path",
                        str(worker_a_path),
                        "--worker-message-log-path",
                        str(worker_b_path),
                    ]
                )

            payload = json.loads(stdout.getvalue())
            after_dispatch = dispatch_path.read_text(encoding="utf-8")
            after_worker_a = worker_a_path.read_text(encoding="utf-8")
            after_worker_b = worker_b_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["command"], "collect-local-results")
        self.assertEqual(payload["dispatch_message_log_path"], str(dispatch_path))
        self.assertEqual(
            payload["worker_message_log_paths"], [str(worker_a_path), str(worker_b_path)]
        )
        self.assertEqual(payload["known_assignment_count"], 1)
        self.assertEqual(payload["reported_result_count"], 1)
        self.assertEqual(payload["contribution_recorded_count"], 1)
        self.assertEqual(payload["missing_assignment_ids"], [])
        self.assertEqual(payload["duplicate_message_ids"], [])
        self.assertEqual(payload["conflicting_message_ids"], [])
        self.assertEqual(
            payload["per_node_contribution_units"],
            {"local-node-a": 1},
        )
        self.assertEqual(payload["total_contribution_units"], 1)
        self.assertEqual(
            payload["collected_message_ids"],
            ["msg-0003", "msg-0004"],
        )
        self.assertEqual(after_dispatch, before_dispatch)
        self.assertEqual(after_worker_a, before_worker_a)
        self.assertEqual(after_worker_b, before_worker_b)

    def test_collect_local_results_errors_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dispatch_path = Path(temp_dir) / "dispatch.json"
            worker_path = Path(temp_dir) / "worker.json"
            dispatch_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            {
                                "message_id": "msg-0001",
                                "message_type": "job_assigned",
                                "sender_node_id": "local-scheduler",
                                "recipient_node_id": "local-node-a",
                                "payload": {"job_id": "echo-1"},
                                "correlation_id": "echo-1",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            worker_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            {
                                "message_id": "msg-0002",
                                "message_type": "job_result_reported",
                                "sender_node_id": "local-node-a",
                                "recipient_node_id": "local-ledger",
                                "payload": {"job_id": "missing"},
                                "correlation_id": "missing",
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
                        "collect-local-results",
                        "--dispatch-message-log-path",
                        str(dispatch_path),
                        "--worker-message-log-path",
                        str(worker_path),
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("unknown assignment", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
