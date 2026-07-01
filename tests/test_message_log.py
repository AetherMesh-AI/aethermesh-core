import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    build_dispatch_message_log_document,
    build_flow_message_log_document,
    build_message_log_document,
    build_replayed_message_log_document,
    load_message_log_messages,
    load_worker_emitted_messages,
    write_message_log,
)
from aethermesh_core.messages import MeshMessage
from aethermesh_core.models import Job
from aethermesh_core.scheduler import JobAssignment, ScheduledNode
from aethermesh_core.simulation import run_local_simulation


class MessageLogTests(unittest.TestCase):
    def test_build_message_log_document_is_deterministic_and_ordered(self) -> None:
        jobs = [
            Job(job_id="echo-1", job_type="echo", payload={"message": "hello mesh"}),
            Job(
                job_id="text-stats-1",
                job_type="text_stats",
                payload={"text": "hello mesh\nhello node"},
            ),
        ]
        first_simulation = run_local_simulation(
            node_ids=["local-node-a", "local-node-b"], jobs=jobs
        )
        second_simulation = run_local_simulation(
            node_ids=["local-node-a", "local-node-b"], jobs=jobs
        )

        first_document = build_message_log_document(
            simulation=first_simulation,
            jobs=jobs,
            manifest_path="examples/local-batch.json",
        )
        second_document = build_message_log_document(
            simulation=second_simulation,
            jobs=jobs,
            manifest_path="examples/local-batch.json",
        )

        self.assertEqual(first_document, second_document)
        self.assertEqual(first_document["version"], 1)
        self.assertEqual(
            first_document["metadata"],
            {
                "source": "run-local-batch",
                "manifest_path": "examples/local-batch.json",
                "message_count": 10,
                "node_count": 2,
                "job_count": 2,
                "completed_count": 2,
                "failed_count": 0,
                "total_contribution_units": 3,
                "validation_summary": {"valid": 2, "invalid": 0, "unsupported": 0},
                "node_ids": ["local-node-a", "local-node-b"],
                "job_ids": ["echo-1", "text-stats-1"],
            },
        )
        self.assertEqual(
            [message["message_id"] for message in first_document["messages"]],
            [f"msg-{index:04d}" for index in range(1, 11)],
        )
        self.assertEqual(
            first_document["messages"][0]["message_type"], "node_heartbeat"
        )
        self.assertEqual(first_document["messages"][2]["message_type"], "job_assigned")
        self.assertEqual(
            first_document["messages"][3]["message_type"], "job_result_reported"
        )
        self.assertEqual(first_document["messages"][4]["message_type"], "job_validated")
        self.assertEqual(
            first_document["messages"][5]["message_type"], "contribution_recorded"
        )
        self.assertEqual(first_document["messages"][2]["correlation_id"], "echo-1")

        first_json = json.dumps(first_document, indent=2, sort_keys=True) + "\n"
        second_json = json.dumps(second_document, indent=2, sort_keys=True) + "\n"
        self.assertEqual(first_json, second_json)

    def test_write_message_log_uses_stable_json_and_creates_parents(self) -> None:
        document = {
            "version": 1,
            "metadata": {"message_count": 0},
            "messages": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "deep" / "nested" / "messages.json"

            write_message_log(log_path, document)

            persisted = log_path.read_text(encoding="utf-8")

        self.assertEqual(
            persisted, json.dumps(document, indent=2, sort_keys=True) + "\n"
        )

    def test_build_replayed_message_log_document_appends_emitted_messages(self) -> None:
        replayed = [
            MeshMessage(
                message_id="msg-0001",
                message_type="job_assigned",
                sender_node_id="local-scheduler",
                recipient_node_id="local-node-a",
                payload={"job_id": "echo-1", "job_type": "echo"},
                correlation_id="echo-1",
            )
        ]
        emitted = [
            MeshMessage(
                message_id="msg-0002",
                message_type="job_result_reported",
                sender_node_id="local-node-a",
                recipient_node_id="local-ledger",
                payload={"job_id": "echo-1", "status": "completed"},
                correlation_id="echo-1",
            )
        ]

        document = build_replayed_message_log_document(
            replayed_messages=replayed,
            emitted_messages=emitted,
            node_id="local-node-a",
            source_message_log_path="./local-messages.json",
            ledger_path="./local-ledger.json",
            processed_assignment_count=1,
            ignored_message_ids=["msg-0003"],
        )

        self.assertEqual(document["version"], 1)
        self.assertEqual(
            document["metadata"],
            {
                "source": "process-local-inbox",
                "node_id": "local-node-a",
                "source_message_log_path": "./local-messages.json",
                "ledger_path": "./local-ledger.json",
                "message_count": 2,
                "replayed_message_count": 1,
                "emitted_message_count": 1,
                "processed_assignment_count": 1,
                "ignored_message_count": 1,
                "ignored_message_ids": ["msg-0003"],
            },
        )
        self.assertEqual(
            [message["message_id"] for message in document["messages"]],
            ["msg-0001", "msg-0002"],
        )

    def test_build_dispatch_message_log_document_contains_only_dispatch_metadata(
        self,
    ) -> None:
        messages = [
            MeshMessage(
                message_id="msg-0001",
                message_type="node_heartbeat",
                sender_node_id="local-node-a",
                recipient_node_id=None,
                payload={"node_id": "local-node-a"},
            ),
            MeshMessage(
                message_id="msg-0002",
                message_type="job_assigned",
                sender_node_id="local-scheduler",
                recipient_node_id="local-node-a",
                payload={"job_id": "echo-1", "job_type": "echo", "payload": {}},
                correlation_id="echo-1",
            ),
        ]

        document = build_dispatch_message_log_document(
            messages=messages,
            jobs=[Job(job_id="echo-1", job_type="echo", payload={})],
            nodes=[ScheduledNode("local-node-a")],
            assignments=[JobAssignment(job_id="echo-1", node_id="local-node-a")],
            manifest_path="examples/local-batch.json",
        )

        self.assertEqual(document["version"], 1)
        self.assertEqual(
            document["metadata"],
            {
                "source": "dispatch-local-batch",
                "manifest_path": "examples/local-batch.json",
                "message_count": 2,
                "node_count": 1,
                "job_count": 1,
                "assignment_count": 1,
                "node_ids": ["local-node-a"],
                "job_ids": ["echo-1"],
                "assigned_node_ids": ["local-node-a"],
            },
        )
        self.assertNotIn("completed_count", document["metadata"])
        self.assertNotIn("total_contribution_units", document["metadata"])
        self.assertEqual(
            [message["message_type"] for message in document["messages"]],
            ["node_heartbeat", "job_assigned"],
        )

    def test_build_flow_message_log_document_merges_dispatch_then_emitted_by_node_order(
        self,
    ) -> None:
        dispatch_messages = [
            MeshMessage(
                message_id="msg-0001",
                message_type="job_assigned",
                sender_node_id="local-scheduler",
                recipient_node_id="local-node-a",
                payload={"job_id": "echo-1", "job_type": "echo", "payload": {}},
                correlation_id="echo-1",
            )
        ]
        emitted_messages_by_node = {
            "local-node-b": [
                MeshMessage(
                    message_id="msg-0005",
                    message_type="job_result_reported",
                    sender_node_id="local-node-b",
                    recipient_node_id="local-ledger",
                    payload={"job_id": "echo-2", "status": "completed"},
                    correlation_id="echo-2",
                )
            ],
            "local-node-a": [
                MeshMessage(
                    message_id="msg-0002",
                    message_type="job_result_reported",
                    sender_node_id="local-node-a",
                    recipient_node_id="local-ledger",
                    payload={"job_id": "echo-1", "status": "completed"},
                    correlation_id="echo-1",
                ),
                MeshMessage(
                    message_id="msg-0003",
                    message_type="job_validated",
                    sender_node_id="local-node-a",
                    recipient_node_id="local-ledger",
                    payload={"job_id": "echo-1", "node_id": "local-node-a"},
                    correlation_id="echo-1",
                ),
                MeshMessage(
                    message_id="msg-0004",
                    message_type="contribution_recorded",
                    sender_node_id="local-ledger",
                    recipient_node_id="local-node-a",
                    payload={"job_id": "echo-1", "contribution_units": 1},
                    correlation_id="echo-1",
                ),
            ],
        }

        document = build_flow_message_log_document(
            dispatch_messages=dispatch_messages,
            emitted_messages_by_node=emitted_messages_by_node,
            manifest_path="manifest.json",
            dispatch_message_log_path="dispatch-message-log.json",
            ledger_path="ledger.json",
            worker_message_log_paths={
                "local-node-a": "worker-message-logs/local-node-a.json",
                "local-node-b": "worker-message-logs/local-node-b.json",
                "local-node-c": "worker-message-logs/local-node-c.json",
            },
            available_node_ids=["local-node-a", "local-node-b"],
            offline_node_ids=["local-node-c"],
            processed_node_ids=["local-node-a", "local-node-b"],
            processed_assignment_count=2,
            skipped_processed_assignment_count=0,
            total_contribution_units=2,
        )

        self.assertEqual(document["version"], 1)
        self.assertEqual(
            document["metadata"],
            {
                "source": "run-local-flow",
                "manifest_path": "manifest.json",
                "dispatch_message_log_path": "dispatch-message-log.json",
                "ledger_path": "ledger.json",
                "worker_message_log_paths": {
                    "local-node-a": "worker-message-logs/local-node-a.json",
                    "local-node-b": "worker-message-logs/local-node-b.json",
                },
                "available_node_ids": ["local-node-a", "local-node-b"],
                "offline_node_ids": ["local-node-c"],
                "processed_node_ids": ["local-node-a", "local-node-b"],
                "processed_assignment_count": 2,
                "skipped_processed_assignment_count": 0,
                "total_contribution_units": 2,
                "dispatch_message_count": 1,
                "emitted_message_count": 4,
                "message_count": 5,
            },
        )
        self.assertEqual(
            [message["message_id"] for message in document["messages"]],
            ["msg-0001", "msg-0002", "msg-0003", "msg-0004", "msg-0005"],
        )

    def test_build_flow_message_log_document_treats_missing_node_as_empty(self) -> None:
        dispatch_messages = [
            MeshMessage(
                message_id="msg-0001",
                message_type="job_assigned",
                sender_node_id="local-scheduler",
                recipient_node_id="local-node-a",
                payload={"job_id": "echo-1", "job_type": "echo", "payload": {}},
                correlation_id="echo-1",
            )
        ]

        document = build_flow_message_log_document(
            dispatch_messages=dispatch_messages,
            emitted_messages_by_node={},
            manifest_path="manifest.json",
            dispatch_message_log_path="dispatch-message-log.json",
            ledger_path="ledger.json",
            worker_message_log_paths={},
            available_node_ids=["local-node-a"],
            offline_node_ids=[],
            processed_node_ids=[],
            processed_assignment_count=0,
            skipped_processed_assignment_count=1,
            total_contribution_units=0,
        )

        self.assertEqual(document["metadata"]["emitted_message_count"], 0)
        self.assertEqual(
            [message["message_id"] for message in document["messages"]], ["msg-0001"]
        )

    def test_load_worker_emitted_messages_skips_replayed_dispatch_messages(
        self,
    ) -> None:
        replayed = [
            MeshMessage(
                message_id="msg-0001",
                message_type="job_assigned",
                sender_node_id="local-scheduler",
                recipient_node_id="local-node-a",
                payload={"job_id": "echo-1", "job_type": "echo"},
                correlation_id="echo-1",
            )
        ]
        emitted = [
            MeshMessage(
                message_id="msg-0002",
                message_type="job_result_reported",
                sender_node_id="local-node-a",
                recipient_node_id="local-ledger",
                payload={"job_id": "echo-1", "status": "completed"},
                correlation_id="echo-1",
            ),
            MeshMessage(
                message_id="msg-0003",
                message_type="contribution_recorded",
                sender_node_id="local-ledger",
                recipient_node_id="local-node-a",
                payload={"job_id": "echo-1", "contribution_units": 1},
                correlation_id="echo-1",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "worker.json"
            write_message_log(
                log_path,
                build_replayed_message_log_document(
                    replayed_messages=replayed,
                    emitted_messages=emitted,
                    node_id="local-node-a",
                    source_message_log_path="dispatch.json",
                ),
            )

            loaded = load_worker_emitted_messages(log_path)

        self.assertEqual(
            [message.message_id for message in loaded], ["msg-0002", "msg-0003"]
        )

    def test_load_worker_emitted_messages_allows_zero_replayed_messages(self) -> None:
        emitted = [
            MeshMessage(
                message_id="msg-0001",
                message_type="job_result_reported",
                sender_node_id="local-node-a",
                recipient_node_id="local-ledger",
                payload={"job_id": "echo-1", "status": "completed"},
                correlation_id="echo-1",
            )
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "worker.json"
            write_message_log(
                log_path,
                build_replayed_message_log_document(
                    replayed_messages=[],
                    emitted_messages=emitted,
                    node_id="local-node-a",
                    source_message_log_path="dispatch.json",
                    processed_assignment_count=0,
                ),
            )

            loaded = load_worker_emitted_messages(log_path)

        self.assertEqual([message.message_id for message in loaded], ["msg-0001"])

    def test_write_message_log_failure_preserves_existing_path(self) -> None:
        document = {
            "version": 1,
            "metadata": {"message_count": 0},
            "messages": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.mkdir()

            with self.assertRaises(MessageLogPersistenceError) as cm:
                write_message_log(log_path, document)

            self.assertTrue(log_path.is_dir())
            self.assertEqual(list(Path(temp_dir).glob(".messages.json.*.tmp")), [])

        self.assertIn("could not write message log file", str(cm.exception))

    def test_load_message_log_messages_returns_validated_messages_without_writing(
        self,
    ) -> None:
        document = {
            "version": 1,
            "metadata": {"message_count": 1},
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
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            original = json.dumps(document, indent=2, sort_keys=True) + "\n"
            log_path.write_text(original, encoding="utf-8")
            before_mtime = log_path.stat().st_mtime_ns

            messages = load_message_log_messages(log_path)

            after_mtime = log_path.stat().st_mtime_ns
            after_contents = log_path.read_text(encoding="utf-8")

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].message_id, "msg-0001")
        self.assertEqual(messages[0].message_type, "job_assigned")
        self.assertEqual(messages[0].sender_node_id, "local-scheduler")
        self.assertEqual(messages[0].recipient_node_id, "local-node-a")
        self.assertEqual(after_mtime, before_mtime)
        self.assertEqual(after_contents, original)

    def test_load_message_log_messages_rejects_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "missing.json"

            with self.assertRaises(MessageLogPersistenceError) as cm:
                load_message_log_messages(log_path)

        self.assertIn("message log file does not exist", str(cm.exception))

    def test_load_message_log_messages_rejects_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.write_text("not-json", encoding="utf-8")

            with self.assertRaises(MessageLogPersistenceError) as cm:
                load_message_log_messages(log_path)

        self.assertIn("message log JSON is malformed", str(cm.exception))

    def test_load_message_log_messages_rejects_non_object_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.write_text("[]", encoding="utf-8")

            with self.assertRaises(MessageLogPersistenceError) as cm:
                load_message_log_messages(log_path)

        self.assertIn("message log JSON must be an object", str(cm.exception))

    def test_load_message_log_messages_rejects_unsupported_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.write_text(
                json.dumps({"version": 2, "messages": []}), encoding="utf-8"
            )

            with self.assertRaises(MessageLogPersistenceError) as cm:
                load_message_log_messages(log_path)

        self.assertIn("message log JSON must contain version 1", str(cm.exception))

    def test_load_message_log_messages_rejects_bool_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.write_text(
                json.dumps({"version": True, "messages": []}), encoding="utf-8"
            )

            with self.assertRaises(MessageLogPersistenceError) as cm:
                load_message_log_messages(log_path)

        self.assertIn("message log JSON must contain version 1", str(cm.exception))

    def test_load_message_log_messages_rejects_missing_or_non_list_messages(
        self,
    ) -> None:
        for document in ({"version": 1}, {"version": 1, "messages": {}}):
            with (
                self.subTest(document=document),
                tempfile.TemporaryDirectory() as temp_dir,
            ):
                log_path = Path(temp_dir) / "messages.json"
                log_path.write_text(json.dumps(document), encoding="utf-8")

                with self.assertRaises(MessageLogPersistenceError) as cm:
                    load_message_log_messages(log_path)

                self.assertIn(
                    "message log JSON field 'messages' must be a list",
                    str(cm.exception),
                )

    def test_load_message_log_messages_rejects_invalid_message_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            log_path.write_text(
                json.dumps({"version": 1, "messages": [{"message_id": "msg-0001"}]}),
                encoding="utf-8",
            )

            with self.assertRaises(MessageLogPersistenceError) as cm:
                load_message_log_messages(log_path)

        self.assertIn("message log entry 0 is invalid", str(cm.exception))

    def test_load_message_log_error_messages_are_stable(self) -> None:
        cases = [
            ([], "message log JSON must be an object"),
            (
                {"version": True, "messages": []},
                "message log JSON must contain version 1",
            ),
            ({"version": 1}, "message log JSON field 'messages' must be a list"),
            (
                {"version": 1, "messages": {}},
                "message log JSON field 'messages' must be a list",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "messages.json"
            for document, expected_message in cases:
                with self.subTest(expected_message=expected_message):
                    log_path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertRaises(MessageLogPersistenceError) as cm:
                        load_message_log_messages(log_path)
                    self.assertEqual(str(cm.exception), expected_message)


if __name__ == "__main__":
    unittest.main()
