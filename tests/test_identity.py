import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.identity import IdentityPersistenceError, load_or_create_identity


class IdentityPersistenceTests(unittest.TestCase):
    def test_missing_identity_file_is_created_with_local_node_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "deep" / "nested" / "local-node.json"

            identity = load_or_create_identity(identity_path)
            persisted = json.loads(identity_path.read_text(encoding="utf-8"))

        self.assertTrue(identity.node_id.startswith("local-"))
        self.assertEqual(
            persisted,
            {"version": 1, "node": {"node_id": identity.node_id}},
        )

    def test_existing_identity_file_reuses_node_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            identity_path.write_text(
                json.dumps({"version": 1, "node": {"node_id": "local-stable-node"}}),
                encoding="utf-8",
            )

            identity = load_or_create_identity(identity_path)

        self.assertEqual(identity.node_id, "local-stable-node")

    def test_malformed_identity_json_raises_clear_error_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            identity_path.write_text("{not json", encoding="utf-8")

            with self.assertRaisesRegex(IdentityPersistenceError, "malformed"):
                load_or_create_identity(identity_path)

            self.assertEqual(identity_path.read_text(encoding="utf-8"), "{not json")

    def test_unsupported_identity_version_raises_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            original = json.dumps({"version": 2, "node": {"node_id": "local-future"}})
            identity_path.write_text(original, encoding="utf-8")

            with self.assertRaisesRegex(IdentityPersistenceError, "version 1"):
                load_or_create_identity(identity_path)

            self.assertEqual(identity_path.read_text(encoding="utf-8"), original)

    def test_invalid_identity_node_id_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            identity_path.write_text(
                json.dumps({"version": 1, "node": {"node_id": ""}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(IdentityPersistenceError, "node.node_id"):
                load_or_create_identity(identity_path)

    def test_identity_error_messages_are_stable(self) -> None:
        cases = [
            ([], "identity JSON must be an object"),
            (
                {"version": 2, "node": {"node_id": "local-future"}},
                "identity JSON must contain version 1",
            ),
            (
                {"version": 1, "node": []},
                "identity JSON field 'node' must be an object",
            ),
            (
                {"version": 1, "node": {"node_id": ""}},
                "identity JSON field 'node.node_id' must be a non-empty string",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            identity_path = Path(temp_dir) / "local-node.json"
            for document, expected_message in cases:
                with self.subTest(expected_message=expected_message):
                    identity_path.write_text(json.dumps(document), encoding="utf-8")
                    with self.assertRaises(IdentityPersistenceError) as cm:
                        load_or_create_identity(identity_path)
                    self.assertEqual(str(cm.exception), expected_message)


if __name__ == "__main__":
    unittest.main()
