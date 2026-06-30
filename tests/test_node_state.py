import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.node_state import (
    LocalNodeProcessingState,
    NodeStatePersistenceError,
    load_node_processing_state,
    save_node_processing_state,
)


class NodeStateTests(unittest.TestCase):
    def test_missing_state_loads_empty_for_expected_node(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "node-state.json"

            state = load_node_processing_state(state_path, expected_node_id="node-a")

        self.assertEqual(state.node_id, "node-a")
        self.assertEqual(state.processed_message_ids, [])
        self.assertEqual(state.processed_assignment_count, 0)

    def test_save_and_load_state_preserves_order_and_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "nested" / "node-state.json"
            state = LocalNodeProcessingState(
                node_id="node-a",
                processed_message_ids=["msg-0001", "msg-0003"],
                extra_fields={"note": "future metadata"},
            )

            save_node_processing_state(state_path, state)
            loaded = load_node_processing_state(state_path, expected_node_id="node-a")
            persisted = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(loaded.node_id, "node-a")
        self.assertEqual(loaded.processed_message_ids, ["msg-0001", "msg-0003"])
        self.assertEqual(loaded.extra_fields, {"note": "future metadata"})
        self.assertEqual(persisted["version"], 1)
        self.assertEqual(persisted["processed_assignment_count"], 2)
        self.assertEqual(persisted["processed_message_ids"], ["msg-0001", "msg-0003"])

    def test_malformed_json_is_rejected_without_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "node-state.json"
            state_path.write_text("not-json", encoding="utf-8")

            with self.assertRaisesRegex(NodeStatePersistenceError, "malformed"):
                load_node_processing_state(state_path, expected_node_id="node-a")

            self.assertEqual(state_path.read_text(encoding="utf-8"), "not-json")

    def test_missing_required_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "node-state.json"
            state_path.write_text(json.dumps({"version": 1}), encoding="utf-8")

            with self.assertRaisesRegex(
                NodeStatePersistenceError, "missing required field"
            ):
                load_node_processing_state(state_path, expected_node_id="node-a")

    def test_wrong_field_types_are_rejected(self) -> None:
        cases = [
            {
                "version": 1,
                "node_id": 7,
                "processed_message_ids": [],
                "processed_assignment_count": 0,
            },
            {
                "version": 1,
                "node_id": "node-a",
                "processed_message_ids": "msg-1",
                "processed_assignment_count": 0,
            },
            {
                "version": 1,
                "node_id": "node-a",
                "processed_message_ids": ["msg-1"],
                "processed_assignment_count": "1",
            },
        ]
        for document in cases:
            with self.subTest(document=document):
                with tempfile.TemporaryDirectory() as temp_dir:
                    state_path = Path(temp_dir) / "node-state.json"
                    state_path.write_text(json.dumps(document), encoding="utf-8")

                    with self.assertRaises(NodeStatePersistenceError):
                        load_node_processing_state(
                            state_path, expected_node_id="node-a"
                        )

    def test_duplicate_processed_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "node-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "node_id": "node-a",
                        "processed_message_ids": ["msg-0001", "msg-0001"],
                        "processed_assignment_count": 2,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(NodeStatePersistenceError, "duplicate"):
                load_node_processing_state(state_path, expected_node_id="node-a")

    def test_unsupported_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "node-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "version": 2,
                        "node_id": "node-a",
                        "processed_message_ids": [],
                        "processed_assignment_count": 0,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(NodeStatePersistenceError, "version 1"):
                load_node_processing_state(state_path, expected_node_id="node-a")

    def test_wrong_node_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "node-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "node_id": "node-b",
                        "processed_message_ids": [],
                        "processed_assignment_count": 0,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(NodeStatePersistenceError, "node-b"):
                load_node_processing_state(state_path, expected_node_id="node-a")

    def test_count_must_match_unique_processed_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "node-state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "node_id": "node-a",
                        "processed_message_ids": ["msg-0001"],
                        "processed_assignment_count": 2,
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(NodeStatePersistenceError, "must equal"):
                load_node_processing_state(state_path, expected_node_id="node-a")


if __name__ == "__main__":
    unittest.main()
