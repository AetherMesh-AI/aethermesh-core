import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.local_runtime_config import (
    LocalRuntimeConfigError,
    default_local_runtime_config_document,
    load_local_runtime_config,
    parse_local_runtime_config_document,
)


class LocalRuntimeConfigTests(unittest.TestCase):
    def test_loads_default_local_runtime_config_with_stable_creator_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document = default_local_runtime_config_document(
                creator_node_id="creator-node-1"
            )
            (root / "local-runtime-config.json").write_text(
                json.dumps(document), encoding="utf-8"
            )

            config = load_local_runtime_config(
                root, expected_creator_node_id="creator-node-1"
            )

            self.assertEqual(config.creator_node_id, "creator-node-1")
            self.assertEqual(
                config.relative_ref(config.identity_path), "identity/creator-node.json"
            )
            self.assertEqual(
                config.relative_ref(config.manifest_path),
                "manifests/local-node-manifest.json",
            )
            self.assertEqual(
                config.relative_ref(config.validation_receipts_dir), "receipts"
            )
            self.assertEqual(config.relative_ref(config.lineage_dir), "lineage")
            self.assertEqual(
                config.relative_ref(config.contribution_attribution_dir),
                "contributions",
            )
            self.assertIn("do not regenerate", str(document["notes"]).lower())

    def test_missing_required_config_field_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document = default_local_runtime_config_document(
                creator_node_id="creator-node-1"
            )
            del document["manifest_path"]
            (root / "local-runtime-config.json").write_text(
                json.dumps(document), encoding="utf-8"
            )

            with self.assertRaisesRegex(
                LocalRuntimeConfigError, "missing required field 'manifest_path'"
            ):
                load_local_runtime_config(root)

    def test_malformed_or_nonlocal_paths_fail_clearly(self) -> None:
        document = default_local_runtime_config_document(creator_node_id="creator")
        document["lineage_dir"] = "../lineage"

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                LocalRuntimeConfigError, "lineage_dir.*local relative path"
            ):
                parse_local_runtime_config_document(Path(temp_dir), document)

        document = default_local_runtime_config_document(creator_node_id="creator")
        document["creator_node_id"] = "other"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "local-runtime-config.json").write_text(
                json.dumps(document), encoding="utf-8"
            )
            with self.assertRaisesRegex(
                LocalRuntimeConfigError, "creator_node_id does not match"
            ):
                load_local_runtime_config(root, expected_creator_node_id="creator")


if __name__ == "__main__":
    unittest.main()
