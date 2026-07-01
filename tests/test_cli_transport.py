import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from aethermesh_core.cli import main


class LocalTransportCliTests(unittest.TestCase):
    def _write_manifest(self, path: Path, jobs: list[dict[str, object]]) -> None:
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "nodes": ["manifest-node-ignored"],
                    "jobs": jobs,
                }
            ),
            encoding="utf-8",
        )

    def _write_peer_log(self, path: Path, peers: list[dict[str, object]]) -> None:
        path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "messages": [
                        {
                            "message_id": f"msg-{index:04d}",
                            "message_type": "node_heartbeat",
                            "sender_node_id": str(peer["node_id"]),
                            "recipient_node_id": None,
                            "payload": {
                                "node_id": peer["node_id"],
                                "status": peer.get("status", "available"),
                                "heartbeat_sequence": index,
                                "heartbeat_count": 1,
                                "capabilities": peer.get("capabilities", ["echo"]),
                            },
                            "correlation_id": None,
                        }
                        for index, peer in enumerate(peers, 1)
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_run_peer_transport_flow_happy_path_uses_peer_roster_and_audits(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            peer_log_path = Path(temp_dir) / "peers.json"
            output_dir = Path(temp_dir) / "flow"
            self._write_manifest(
                manifest_path,
                [
                    {
                        "job_id": "echo-1",
                        "job_type": "echo",
                        "payload": {"message": "peer one"},
                    },
                    {
                        "job_id": "echo-2",
                        "job_type": "echo",
                        "payload": {"message": "peer two"},
                    },
                ],
            )
            self._write_peer_log(
                peer_log_path,
                [
                    {"node_id": "peer-a", "capabilities": ["echo"]},
                    {"node_id": "peer-b", "capabilities": ["echo"]},
                ],
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-peer-transport-flow",
                        "--peer-log-path",
                        str(peer_log_path),
                        "--manifest",
                        str(manifest_path),
                        "--output-dir",
                        str(output_dir),
                    ]
                )
            audit_stdout = io.StringIO()
            with contextlib.redirect_stdout(audit_stdout):
                audit_exit = main(["audit-local-flow", "--output-dir", str(output_dir)])
            payload = json.loads(stdout.getvalue())
            audit_payload = json.loads(audit_stdout.getvalue())
            flow_log = json.loads(
                (output_dir / "flow-message-log.json").read_text(encoding="utf-8")
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(audit_exit, 0)
        self.assertEqual(payload["command"], "run-peer-transport-flow")
        self.assertEqual(payload["peer_log_path"], str(peer_log_path))
        self.assertEqual(payload["roster_source"], "heartbeat_peer_log")
        self.assertEqual(payload["available_node_ids"], ["peer-a", "peer-b"])
        self.assertEqual(payload["processed_node_ids"], ["peer-a", "peer-b"])
        self.assertEqual(payload["processed_assignment_count"], 2)
        self.assertEqual(payload["transport_inbox_count"], 2)
        self.assertEqual(audit_payload["ok"], True)
        self.assertEqual(flow_log["metadata"]["source"], "run-peer-transport-flow")
        self.assertEqual(flow_log["metadata"]["peer_log_path"], str(peer_log_path))

    def test_run_peer_transport_flow_skips_offline_peer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            peer_log_path = Path(temp_dir) / "peers.json"
            output_dir = Path(temp_dir) / "flow"
            self._write_manifest(
                manifest_path,
                [
                    {
                        "job_id": "echo-1",
                        "job_type": "echo",
                        "payload": {"message": "online only"},
                    }
                ],
            )
            self._write_peer_log(
                peer_log_path,
                [
                    {
                        "node_id": "peer-a",
                        "status": "available",
                        "capabilities": ["echo"],
                    },
                    {
                        "node_id": "peer-b",
                        "status": "offline",
                        "capabilities": ["echo"],
                    },
                ],
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-peer-transport-flow",
                        "--peer-log-path",
                        str(peer_log_path),
                        "--manifest",
                        str(manifest_path),
                        "--output-dir",
                        str(output_dir),
                    ]
                )
            payload = json.loads(stdout.getvalue())
            offline_inbox_exists = (
                output_dir / "transport" / "inboxes" / "peer-b.json"
            ).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["available_node_ids"], ["peer-a"])
        self.assertEqual(payload["offline_node_ids"], ["peer-b"])
        self.assertEqual(payload["processed_node_ids"], ["peer-a"])
        self.assertFalse(offline_inbox_exists)

    def test_run_peer_transport_flow_routes_by_capability(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            peer_log_path = Path(temp_dir) / "peers.json"
            output_dir = Path(temp_dir) / "flow"
            self._write_manifest(
                manifest_path,
                [
                    {
                        "job_id": "stats-1",
                        "job_type": "text_stats",
                        "payload": {"text": "a b"},
                    },
                    {
                        "job_id": "echo-1",
                        "job_type": "echo",
                        "payload": {"message": "e"},
                    },
                ],
            )
            self._write_peer_log(
                peer_log_path,
                [
                    {"node_id": "echo-peer", "capabilities": ["echo"]},
                    {"node_id": "stats-peer", "capabilities": ["text_stats"]},
                ],
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-peer-transport-flow",
                        "--peer-log-path",
                        str(peer_log_path),
                        "--manifest",
                        str(manifest_path),
                        "--output-dir",
                        str(output_dir),
                    ]
                )
            payload = json.loads(stdout.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            payload["dispatch_summary"]["assignments"],
            [
                {"job_id": "stats-1", "node_id": "stats-peer"},
                {"job_id": "echo-1", "node_id": "echo-peer"},
            ],
        )

    def test_run_peer_transport_flow_failures_do_not_create_output_artifacts(
        self,
    ) -> None:
        cases = [
            ("empty peer log", {"version": 1, "messages": []}, "no heartbeat peers"),
            ("malformed peer log", "not-json", "message log JSON is malformed"),
            (
                "all offline",
                None,
                "no available nodes for local job assignment",
            ),
            (
                "no capable peer",
                None,
                "no available capable node",
            ),
        ]
        for name, peer_document, expected_error in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                manifest_path = Path(temp_dir) / "manifest.json"
                peer_log_path = Path(temp_dir) / "peers.json"
                output_dir = Path(temp_dir) / "flow"
                self._write_manifest(
                    manifest_path,
                    [
                        {
                            "job_id": "echo-1",
                            "job_type": "echo",
                            "payload": {"message": "x"},
                        }
                    ],
                )
                if peer_document == "not-json":
                    peer_log_path.write_text("not-json", encoding="utf-8")
                elif peer_document is not None:
                    peer_log_path.write_text(
                        json.dumps(peer_document), encoding="utf-8"
                    )
                elif name == "all offline":
                    self._write_peer_log(
                        peer_log_path,
                        [
                            {
                                "node_id": "peer-a",
                                "status": "offline",
                                "capabilities": ["echo"],
                            }
                        ],
                    )
                else:
                    self._write_peer_log(
                        peer_log_path,
                        [
                            {
                                "node_id": "peer-a",
                                "status": "available",
                                "capabilities": ["text_stats"],
                            }
                        ],
                    )

                stdout = io.StringIO()
                stderr = io.StringIO()
                with (
                    contextlib.redirect_stdout(stdout),
                    contextlib.redirect_stderr(stderr),
                ):
                    exit_code = main(
                        [
                            "run-peer-transport-flow",
                            "--peer-log-path",
                            str(peer_log_path),
                            "--manifest",
                            str(manifest_path),
                            "--output-dir",
                            str(output_dir),
                        ]
                    )

                self.assertEqual(exit_code, 1)
                self.assertEqual(stdout.getvalue(), "")
                self.assertIn(expected_error, stderr.getvalue())
                self.assertFalse(output_dir.exists())

    def test_run_local_transport_flow_uses_default_transport_dir_and_audits(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            output_dir = Path(temp_dir) / "flow"
            default_transport_dir = output_dir / "transport"
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

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-local-transport-flow",
                        "--manifest",
                        str(manifest_path),
                        "--output-dir",
                        str(output_dir),
                    ]
                )
            audit_stdout = io.StringIO()
            with contextlib.redirect_stdout(audit_stdout):
                audit_exit = main(["audit-local-flow", "--output-dir", str(output_dir)])

            payload = json.loads(stdout.getvalue())
            audit_payload = json.loads(audit_stdout.getvalue())
            ledger_exists = (output_dir / "ledger.json").exists()
            receipts_exists = (output_dir / "receipts.json").exists()
            dispatch_log_exists = (output_dir / "dispatch-message-log.json").exists()
            flow_log_exists = (output_dir / "flow-message-log.json").exists()
            worker_log_exists = (
                output_dir / "worker-message-logs" / "local-node-a.json"
            ).exists()
            node_state_exists = (
                output_dir / "node-state" / "local-node-a.json"
            ).exists()
            transport_inbox_exists = (
                default_transport_dir / "inboxes" / "local-node-a.json"
            ).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(audit_exit, 0)
        self.assertEqual(payload["command"], "run-local-flow")
        self.assertEqual(payload["transport_dir"], str(default_transport_dir))
        self.assertEqual(payload["transport_inbox_count"], 2)
        self.assertEqual(payload["processed_assignment_count"], 2)
        self.assertEqual(audit_payload["ok"], True)
        self.assertTrue(ledger_exists)
        self.assertTrue(receipts_exists)
        self.assertTrue(dispatch_log_exists)
        self.assertTrue(flow_log_exists)
        self.assertTrue(worker_log_exists)
        self.assertTrue(node_state_exists)
        self.assertTrue(transport_inbox_exists)

    def test_run_local_transport_flow_accepts_explicit_transport_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            output_dir = Path(temp_dir) / "flow"
            transport_dir = Path(temp_dir) / "custom-transport"
            default_transport_dir = output_dir / "transport"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
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

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run-local-transport-flow",
                        "--manifest",
                        str(manifest_path),
                        "--output-dir",
                        str(output_dir),
                        "--transport-dir",
                        str(transport_dir),
                    ]
                )

            payload = json.loads(stdout.getvalue())
            explicit_inbox_exists = (
                transport_dir / "inboxes" / "local-node-a.json"
            ).exists()
            default_transport_exists = default_transport_dir.exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["command"], "run-local-flow")
        self.assertEqual(payload["transport_dir"], str(transport_dir))
        self.assertTrue(explicit_inbox_exists)
        self.assertFalse(default_transport_exists)

    def test_run_local_transport_flow_reports_runtime_errors(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch(
                "aethermesh_core.cli.run_local_transport_flow",
                side_effect=ValueError("bad transport setup"),
            ),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = main(
                [
                    "run-local-transport-flow",
                    "--manifest",
                    "manifest.json",
                    "--output-dir",
                    "out",
                ]
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("error: bad transport setup", stderr.getvalue())

    def test_run_local_flow_transport_handles_available_node_without_assignments(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            output_dir = Path(temp_dir) / "flow"
            transport_dir = Path(temp_dir) / "transport"
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
                        "run-local-flow",
                        "--manifest",
                        str(manifest_path),
                        "--output-dir",
                        str(output_dir),
                        "--transport-dir",
                        str(transport_dir),
                    ]
                )

            payload = json.loads(stdout.getvalue())
            node_b_inbox = json.loads(
                (transport_dir / "inboxes" / "local-node-b.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            payload["available_node_ids"], ["local-node-a", "local-node-b"]
        )
        self.assertEqual(
            payload["processed_node_ids"], ["local-node-a", "local-node-b"]
        )
        self.assertEqual(payload["processed_assignment_count"], 1)
        self.assertEqual(payload["transport_inbox_count"], 1)
        self.assertEqual(node_b_inbox["node_id"], "local-node-b")
        self.assertEqual(node_b_inbox["messages"], [])

    def test_run_local_flow_uses_transport_inboxes_and_audits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            output_dir = Path(temp_dir) / "flow"
            transport_dir = Path(temp_dir) / "transport"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": [
                            {"node_id": "local-node-a", "status": "available"},
                            {"node_id": "local-node-b", "status": "offline"},
                            {"node_id": "local-node-c", "status": "available"},
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

            first_stdout = io.StringIO()
            with contextlib.redirect_stdout(first_stdout):
                first_exit = main(
                    [
                        "run-local-flow",
                        "--manifest",
                        str(manifest_path),
                        "--output-dir",
                        str(output_dir),
                        "--transport-dir",
                        str(transport_dir),
                    ]
                )
            audit_stdout = io.StringIO()
            with contextlib.redirect_stdout(audit_stdout):
                audit_exit = main(["audit-local-flow", "--output-dir", str(output_dir)])
            second_stdout = io.StringIO()
            with contextlib.redirect_stdout(second_stdout):
                second_exit = main(
                    [
                        "run-local-flow",
                        "--manifest",
                        str(manifest_path),
                        "--output-dir",
                        str(output_dir),
                        "--transport-dir",
                        str(transport_dir),
                    ]
                )

            first_payload = json.loads(first_stdout.getvalue())
            audit_payload = json.loads(audit_stdout.getvalue())
            second_payload = json.loads(second_stdout.getvalue())
            ledger = json.loads(
                (output_dir / "ledger.json").read_text(encoding="utf-8")
            )
            node_a_inbox = json.loads(
                (transport_dir / "inboxes" / "local-node-a.json").read_text(
                    encoding="utf-8"
                )
            )
            node_c_inbox = json.loads(
                (transport_dir / "inboxes" / "local-node-c.json").read_text(
                    encoding="utf-8"
                )
            )
            offline_inbox_exists = (
                transport_dir / "inboxes" / "local-node-b.json"
            ).exists()
            offline_worker_log_exists = (
                output_dir / "worker-message-logs" / "local-node-b.json"
            ).exists()

        self.assertEqual(first_exit, 0)
        self.assertEqual(audit_exit, 0)
        self.assertEqual(second_exit, 0)
        self.assertEqual(first_payload["transport_dir"], str(transport_dir))
        self.assertEqual(first_payload["transport_inbox_count"], 2)
        self.assertEqual(
            first_payload["transport_inbox_paths"],
            {
                "local-node-a": str(transport_dir / "inboxes" / "local-node-a.json"),
                "local-node-c": str(transport_dir / "inboxes" / "local-node-c.json"),
            },
        )
        self.assertEqual(
            first_payload["available_node_ids"], ["local-node-a", "local-node-c"]
        )
        self.assertEqual(first_payload["offline_node_ids"], ["local-node-b"])
        self.assertEqual(
            first_payload["processed_node_ids"], ["local-node-a", "local-node-c"]
        )
        self.assertEqual(first_payload["processed_assignment_count"], 3)
        self.assertEqual(second_payload["processed_assignment_count"], 0)
        self.assertEqual(second_payload["skipped_processed_assignment_count"], 3)
        self.assertEqual(second_payload["transport_inbox_count"], 2)
        self.assertEqual(audit_payload["ok"], True)
        self.assertEqual(audit_payload["counts"]["ledger_records"], 3)
        self.assertEqual(len(ledger["records"]), 3)
        self.assertEqual(node_a_inbox["node_id"], "local-node-a")
        self.assertEqual(node_c_inbox["node_id"], "local-node-c")
        self.assertEqual(
            [message["recipient_node_id"] for message in node_a_inbox["messages"]],
            ["local-node-a", "local-node-a"],
        )
        self.assertEqual(
            [message["recipient_node_id"] for message in node_c_inbox["messages"]],
            ["local-node-c"],
        )
        self.assertFalse(offline_inbox_exists)
        self.assertFalse(offline_worker_log_exists)

    def test_materialize_local_inboxes_and_process_transport_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            dispatch_path = Path(temp_dir) / "dispatch.json"
            transport_dir = Path(temp_dir) / "transport"
            ledger_path = Path(temp_dir) / "ledger.json"
            state_path = Path(temp_dir) / "node-a-state.json"
            outbox_path = transport_dir / "outboxes" / "local-node-a.json"
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
        self.assertNotIn("transport_outbox_path", processed)
        self.assertNotIn("transport_outbox_message_count", processed)
        self.assertFalse(outbox_path.exists())
        self.assertEqual(rerun["processed_assignment_count"], 0)
        self.assertEqual(rerun["skipped_processed_message_ids"], ["msg-0003"])
        self.assertEqual(len(ledger["records"]), 1)
        self.assertEqual(ledger["records"][0]["node_id"], "local-node-a")

    def test_transport_inbox_outbox_opt_in_writes_emitted_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transport_dir = Path(temp_dir) / "transport"
            inbox_path = transport_dir / "inboxes" / "local-node-a.json"
            outbox_path = transport_dir / "outboxes" / "local-node-a.json"
            ledger_path = Path(temp_dir) / "ledger.json"
            output_log_path = Path(temp_dir) / "worker-log.json"
            inbox_path.parent.mkdir(parents=True)
            inbox_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "node_id": "local-node-a",
                        "messages": [
                            {
                                "message_id": "msg-assign-1",
                                "message_type": "job_assigned",
                                "sender_node_id": "scheduler",
                                "recipient_node_id": "local-node-a",
                                "payload": {
                                    "job_id": "echo-1",
                                    "job_type": "echo",
                                    "payload": {"message": "hello outbox"},
                                },
                                "correlation_id": "echo-1",
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
                        "local-node-a",
                        "--transport-dir",
                        str(transport_dir),
                        "--ledger-path",
                        str(ledger_path),
                        "--output-message-log-path",
                        str(output_log_path),
                        "--write-transport-outbox",
                    ]
                )
            processed = json.loads(stdout.getvalue())
            outbox = json.loads(outbox_path.read_text(encoding="utf-8"))
            worker_log = json.loads(output_log_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(processed["processed_assignment_count"], 1)
        self.assertEqual(processed["transport_outbox_path"], str(outbox_path))
        self.assertEqual(processed["transport_outbox_message_count"], 2)
        self.assertEqual(outbox["version"], 1)
        self.assertEqual(outbox["node_id"], "local-node-a")
        self.assertEqual(outbox["source_inbox_path"], str(inbox_path))
        self.assertEqual(outbox["processed_assignment_count"], 1)
        self.assertEqual(
            [message["message_type"] for message in outbox["messages"]],
            ["job_result_reported", "job_validated"],
        )
        self.assertEqual(
            [message["sender_node_id"] for message in outbox["messages"]],
            ["local-node-a", "local-node-a"],
        )
        self.assertNotIn(
            "msg-assign-1", [message["message_id"] for message in outbox["messages"]]
        )
        self.assertEqual(len(worker_log["messages"]), 4)

    def test_collect_local_outboxes_cli_collects_worker_outbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transport_dir = Path(temp_dir) / "transport"
            outbox_dir = transport_dir / "outboxes"
            outbox_dir.mkdir(parents=True)
            output_path = Path(temp_dir) / "collected.json"
            (outbox_dir / "node-b.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "node_id": "node-b",
                        "source_inbox_path": "inbox-b.json",
                        "processed_assignment_count": 1,
                        "messages": [
                            {
                                "message_id": "msg-b-result",
                                "message_type": "job_result_reported",
                                "sender_node_id": "node-b",
                                "recipient_node_id": "scheduler",
                                "payload": {"job_id": "job-b", "status": "completed"},
                                "correlation_id": "job-b",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (outbox_dir / "node-a.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "node_id": "node-a",
                        "source_inbox_path": "inbox-a.json",
                        "processed_assignment_count": 1,
                        "messages": [
                            {
                                "message_id": "msg-a-result",
                                "message_type": "job_result_reported",
                                "sender_node_id": "node-a",
                                "recipient_node_id": "scheduler",
                                "payload": {"job_id": "job-a", "status": "completed"},
                                "correlation_id": "job-a",
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
                        "collect-local-outboxes",
                        "--transport-dir",
                        str(transport_dir),
                        "--message-log-path",
                        str(output_path),
                    ]
                )
            payload = json.loads(stdout.getvalue())
            collected = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["source"], "collect-local-outboxes")
        self.assertEqual(payload["outbox_count"], 2)
        self.assertEqual(payload["node_ids"], ["node-a", "node-b"])
        self.assertEqual(payload["message_count"], 2)
        self.assertEqual(collected["metadata"], payload)
        self.assertEqual(
            [message["message_id"] for message in collected["messages"]],
            ["msg-a-result", "msg-b-result"],
        )

    def test_collect_local_outboxes_cli_missing_transport_writes_empty_log(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transport_dir = Path(temp_dir) / "missing"
            output_path = Path(temp_dir) / "collected.json"
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "collect-local-outboxes",
                        "--transport-dir",
                        str(transport_dir),
                        "--message-log-path",
                        str(output_path),
                    ]
                )
            payload = json.loads(stdout.getvalue())
            collected = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["outbox_count"], 0)
        self.assertEqual(payload["message_count"], 0)
        self.assertEqual(payload["node_ids"], [])
        self.assertEqual(collected["messages"], [])

    def test_collect_local_outboxes_cli_error_does_not_overwrite_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            transport_dir = Path(temp_dir) / "transport"
            outbox_dir = transport_dir / "outboxes"
            outbox_dir.mkdir(parents=True)
            output_path = Path(temp_dir) / "collected.json"
            output_path.write_text("original", encoding="utf-8")
            (outbox_dir / "node-a.json").write_text("not-json", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "collect-local-outboxes",
                        "--transport-dir",
                        str(transport_dir),
                        "--message-log-path",
                        str(output_path),
                    ]
                )
            output_contents = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("local transport outbox JSON is malformed", stderr.getvalue())
        self.assertEqual(output_contents, "original")

    def test_transport_outbox_full_loop_can_be_collected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "local-batch.json"
            dispatch_path = Path(temp_dir) / "dispatch.json"
            transport_dir = Path(temp_dir) / "transport"
            ledger_path = Path(temp_dir) / "ledger.json"
            collected_path = Path(temp_dir) / "collected-worker-output.json"
            manifest_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nodes": ["local-node-a"],
                        "jobs": [
                            {
                                "job_id": "echo-1",
                                "job_type": "echo",
                                "payload": {"message": "collect me"},
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            commands = [
                [
                    "dispatch-local-batch",
                    "--manifest",
                    str(manifest_path),
                    "--message-log-path",
                    str(dispatch_path),
                ],
                [
                    "materialize-local-inboxes",
                    "--message-log-path",
                    str(dispatch_path),
                    "--transport-dir",
                    str(transport_dir),
                ],
                [
                    "process-local-inbox",
                    "--node-id",
                    "local-node-a",
                    "--transport-dir",
                    str(transport_dir),
                    "--ledger-path",
                    str(ledger_path),
                    "--write-transport-outbox",
                ],
                [
                    "collect-local-outboxes",
                    "--transport-dir",
                    str(transport_dir),
                    "--message-log-path",
                    str(collected_path),
                ],
            ]
            outputs = []
            for command in commands:
                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    exit_code = main(command)
                self.assertEqual(exit_code, 0)
                outputs.append(json.loads(stdout.getvalue()))
            collected = json.loads(collected_path.read_text(encoding="utf-8"))

        self.assertEqual(outputs[-1]["outbox_count"], 1)
        self.assertEqual(outputs[-1]["node_ids"], ["local-node-a"])
        self.assertEqual(outputs[-1]["message_count"], 2)
        self.assertEqual(
            [message["message_type"] for message in collected["messages"]],
            ["job_result_reported", "job_validated"],
        )

    def test_write_transport_outbox_rejects_message_log_input(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(
                [
                    "process-local-inbox",
                    "--node-id",
                    "local-node-a",
                    "--message-log-path",
                    "messages.json",
                    "--write-transport-outbox",
                ]
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn(
            "--write-transport-outbox requires --transport-dir", stderr.getvalue()
        )

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
            outbox_original = json.dumps({"version": 1, "messages": [], "keep": True})
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
