import json
import tempfile
import unittest
from pathlib import Path


from aethermesh_core.local_transport import (
    LocalTransportError,
    load_local_inbox,
    local_inbox_path,
    materialize_local_inboxes,
    write_local_inbox,
)
from aethermesh_core.messages import MeshMessage


class LocalTransportTests(unittest.TestCase):
    def test_materializes_two_recipient_inboxes_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "dispatch.json"
            transport_dir = Path(temp_dir) / "transport"
            message_log_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            _message_entry(
                                "msg-0001", "node-a", None, "node_heartbeat"
                            ),
                            _message_entry("msg-0002", "scheduler", "node-b"),
                            _message_entry("msg-0003", "scheduler", "node-a"),
                            _message_entry("msg-0004", "scheduler", "node-b"),
                        ],
                    }
                ),
                encoding="utf-8",
            )

            first = materialize_local_inboxes(
                message_log_path=message_log_path, transport_dir=transport_dir
            )
            node_a_path = local_inbox_path(transport_dir, "node-a")
            node_b_path = local_inbox_path(transport_dir, "node-b")
            first_a = node_a_path.read_text(encoding="utf-8")
            first_b = node_b_path.read_text(encoding="utf-8")
            second = materialize_local_inboxes(
                message_log_path=message_log_path, transport_dir=transport_dir
            )
            second_a = node_a_path.read_text(encoding="utf-8")
            second_b = node_b_path.read_text(encoding="utf-8")
            node_a = json.loads(first_a)
            node_b = json.loads(first_b)

        self.assertEqual(first["node_ids"], ["node-a", "node-b"])
        self.assertEqual(first["inbox_count"], 2)
        self.assertEqual(first["message_count"], 3)
        self.assertEqual(first, second)
        self.assertEqual(first_a, second_a)
        self.assertEqual(first_b, second_b)
        self.assertEqual(node_a["version"], 1)
        self.assertEqual(node_a["node_id"], "node-a")
        self.assertEqual(
            [message["message_id"] for message in node_a["messages"]], ["msg-0003"]
        )
        self.assertEqual(
            [message["message_id"] for message in node_b["messages"]],
            ["msg-0002", "msg-0004"],
        )

    def test_load_rejects_wrong_node_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = local_inbox_path(temp_dir, "node-a")
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps({"version": 1, "node_id": "node-b", "messages": []}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(LocalTransportError, "node_id mismatch"):
                load_local_inbox(transport_dir=temp_dir, node_id="node-a")

    def test_load_rejects_malformed_and_unsupported_inboxes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = local_inbox_path(temp_dir, "node-a")
            path.parent.mkdir(parents=True)
            path.write_text("not-json", encoding="utf-8")
            with self.assertRaisesRegex(LocalTransportError, "malformed"):
                load_local_inbox(transport_dir=temp_dir, node_id="node-a")

            path.write_text(
                json.dumps({"version": 2, "node_id": "node-a", "messages": []}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(LocalTransportError, "version 1"):
                load_local_inbox(transport_dir=temp_dir, node_id="node-a")

    def test_load_rejects_duplicate_missing_and_wrong_recipient_entries(self) -> None:
        duplicate = _message("msg-0001", "node-a")
        with tempfile.TemporaryDirectory() as temp_dir:
            write_local_inbox(
                transport_dir=temp_dir,
                node_id="node-a",
                messages=[duplicate],
            )
            path = local_inbox_path(temp_dir, "node-a")
            document = json.loads(path.read_text(encoding="utf-8"))
            document["messages"].append(document["messages"][0])
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(LocalTransportError, "duplicate message_id"):
                load_local_inbox(transport_dir=temp_dir, node_id="node-a")

            document["messages"] = [{"message_type": "job_assigned"}]
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(LocalTransportError, "message_id"):
                load_local_inbox(transport_dir=temp_dir, node_id="node-a")

            document["messages"] = [_message("msg-0002", "node-b").to_dict()]
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaisesRegex(
                LocalTransportError, "recipient_node_id must be node-a"
            ):
                load_local_inbox(transport_dir=temp_dir, node_id="node-a")

    def test_materialize_ignores_broadcast_messages_without_creating_inboxes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "broadcast-only.json"
            transport_dir = Path(temp_dir) / "transport"
            message_log_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            _message_entry(
                                "msg-0001", "node-a", None, "node_heartbeat"
                            ),
                            _message_entry(
                                "msg-0002", "node-b", None, "node_heartbeat"
                            ),
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = materialize_local_inboxes(
                message_log_path=message_log_path, transport_dir=transport_dir
            )

            self.assertEqual(result["inbox_count"], 0)
            self.assertEqual(result["message_count"], 0)
            self.assertEqual(result["node_ids"], [])
            self.assertEqual(result["inbox_paths"], {})
            self.assertFalse((transport_dir / "inboxes").exists())

    def test_materialize_rejects_duplicate_source_message_ids_before_writing(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            message_log_path = Path(temp_dir) / "duplicates.json"
            transport_dir = Path(temp_dir) / "transport"
            message_log_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "messages": [
                            _message_entry("msg-0001", "scheduler", "node-a"),
                            _message_entry("msg-0001", "scheduler", "node-b"),
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                LocalTransportError, "duplicate message_id in source log"
            ):
                materialize_local_inboxes(
                    message_log_path=message_log_path, transport_dir=transport_dir
                )

            self.assertFalse((transport_dir / "inboxes").exists())

    def test_inbox_path_quotes_node_ids_without_changing_loaded_node_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            node_id = "node/a b?c"
            source_path = Path(temp_dir) / "source log.json"
            path = write_local_inbox(
                transport_dir=temp_dir,
                node_id=node_id,
                messages=[_message("msg-quoted", node_id)],
                source_message_log_path=source_path,
            )
            document = json.loads(path.read_text(encoding="utf-8"))
            messages = load_local_inbox(transport_dir=temp_dir, node_id=node_id)

        self.assertEqual(path.name, "node%2Fa%20b%3Fc.json")
        self.assertEqual(document["node_id"], node_id)
        self.assertEqual(document["source_message_log_path"], str(source_path))
        self.assertEqual([message.message_id for message in messages], ["msg-quoted"])


def _message(message_id: str, recipient: str) -> MeshMessage:
    return MeshMessage(
        message_id=message_id,
        message_type="job_assigned",
        sender_node_id="scheduler",
        recipient_node_id=recipient,
        payload={
            "job_id": message_id,
            "job_type": "echo",
            "payload": {"message": message_id},
        },
        correlation_id=message_id,
    )


def _message_entry(
    message_id: str,
    sender: str,
    recipient: str | None,
    message_type: str = "job_assigned",
) -> dict[str, object]:
    payload = (
        {"node_id": sender}
        if message_type == "node_heartbeat"
        else {
            "job_id": message_id,
            "job_type": "echo",
            "payload": {"message": message_id},
        }
    )
    return {
        "message_id": message_id,
        "message_type": message_type,
        "sender_node_id": sender,
        "recipient_node_id": recipient,
        "payload": payload,
        "correlation_id": None if message_type == "node_heartbeat" else message_id,
    }


if __name__ == "__main__":
    unittest.main()
