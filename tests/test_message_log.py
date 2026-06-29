import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.message_log import (
    MessageLogPersistenceError,
    build_message_log_document,
    load_message_log_messages,
    write_message_log,
)
from aethermesh_core.models import Job
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
        self.assertEqual(first_document["metadata"]["source"], "run-local-batch")
        self.assertEqual(first_document["metadata"]["message_count"], 8)
        self.assertEqual(first_document["metadata"]["node_count"], 2)
        self.assertEqual(first_document["metadata"]["job_count"], 2)
        self.assertEqual(first_document["metadata"]["completed_count"], 2)
        self.assertEqual(first_document["metadata"]["failed_count"], 0)
        self.assertEqual(first_document["metadata"]["total_contribution_units"], 2)
        self.assertEqual(first_document["metadata"]["job_ids"], ["echo-1", "text-stats-1"])
        self.assertEqual(
            [message["message_id"] for message in first_document["messages"]],
            [f"msg-{index:04d}" for index in range(1, 9)],
        )
        self.assertEqual(first_document["messages"][0]["message_type"], "node_heartbeat")
        self.assertEqual(first_document["messages"][2]["message_type"], "job_assigned")
        self.assertEqual(first_document["messages"][3]["message_type"], "job_result_reported")
        self.assertEqual(first_document["messages"][4]["message_type"], "contribution_recorded")
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
            log_path = Path(temp_dir) / "nested" / "messages.json"

            write_message_log(log_path, document)

            persisted = log_path.read_text(encoding="utf-8")

        self.assertEqual(persisted, json.dumps(document, indent=2, sort_keys=True) + "\n")

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

    def test_load_message_log_messages_returns_validated_messages_without_writing(self) -> None:
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

    def test_load_message_log_messages_rejects_missing_or_non_list_messages(self) -> None:
        for document in ({"version": 1}, {"version": 1, "messages": {}}):
            with self.subTest(document=document), tempfile.TemporaryDirectory() as temp_dir:
                log_path = Path(temp_dir) / "messages.json"
                log_path.write_text(json.dumps(document), encoding="utf-8")

                with self.assertRaises(MessageLogPersistenceError) as cm:
                    load_message_log_messages(log_path)

                self.assertIn(
                    "message log JSON field 'messages' must be a list", str(cm.exception)
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


if __name__ == "__main__":
    unittest.main()
