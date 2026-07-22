import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from aethermesh_core.expert_manifest import (
    RECEIPT_VERSION,
    ExpertManifestError,
    expert_is_usable,
    load_expert_manifest,
    validate_expert_manifest,
)


ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "examples/model-experts/echo-expert-v0/manifest.json"


class ExpertManifestIdentityTests(unittest.TestCase):
    def test_accepts_model_id_expert_id_or_both(self) -> None:
        expert_only = self._sample()
        validate_expert_manifest(expert_only)

        model_only = self._sample()
        model_only.pop("expert_id")
        model_only["model_id"] = "local-echo-model-v0"
        validate_expert_manifest(model_only)

        both = self._sample()
        both["model_id"] = "local-echo-model-v0"
        validate_expert_manifest(both)

    def test_rejects_missing_blank_or_whitespace_only_identity(self) -> None:
        cases = [
            {},
            {"expert_id": ""},
            {"expert_id": "   "},
            {"model_id": ""},
            {"model_id": "\t"},
        ]
        for identities in cases:
            with self.subTest(identities=identities):
                document = self._sample()
                document.pop("expert_id")
                document.update(identities)
                with self.assertRaisesRegex(
                    ExpertManifestError,
                    "requires at least one non-empty model_id or expert_id",
                ):
                    validate_expert_manifest(document)

    def test_model_id_is_preserved_in_matching_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            artifact = directory / "artifact.txt"
            artifact.write_text("artifact", encoding="utf-8")
            document = self._sample()
            document.pop("expert_id")
            document["model_id"] = "local-echo-model-v0"
            artifact_hash = (
                "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest()
            )
            document["artifact"]["sha256"] = artifact_hash
            document["artifact_hash"] = artifact_hash
            document["lineage"]["derived_artifact_refs"] = ["artifact.txt"]
            document["validation"].update(
                {
                    "status": "passed",
                    "test_command": "python -m unittest",
                    "expected_inputs_ref": "input.json",
                    "receipt_path": "receipt.json",
                    "last_validated_at": "2026-07-18T00:00:01Z",
                    "validator_node_id": "node-validator",
                }
            )
            document["contribution_attribution"].update(
                {
                    "validator_node_id": "node-validator",
                    "receipt_refs": ["receipt.json"],
                }
            )
            manifest = directory / "manifest.json"
            manifest.write_text(json.dumps(document), encoding="utf-8")
            receipt = {
                "receipt_version": RECEIPT_VERSION,
                "name": document["name"],
                "manifest_id": document["manifest_id"],
                "model_id": document["model_id"],
                "creator_node_id": document["creator_node_id"],
                "created_at": document["created_at"],
                "artifact_hash": artifact_hash,
                "validated_at": document["validation"]["last_validated_at"],
                "validator_node_id": document["validation"]["validator_node_id"],
                "status": "passed",
            }
            (directory / "receipt.json").write_text(
                json.dumps(receipt), encoding="utf-8"
            )

            self.assertTrue(expert_is_usable(manifest))
            self.assertEqual(
                json.loads((directory / "receipt.json").read_text(encoding="utf-8"))[
                    "model_id"
                ],
                "local-echo-model-v0",
            )
            self.assertEqual(
                json.loads((directory / "receipt.json").read_text(encoding="utf-8"))[
                    "creator_node_id"
                ],
                document["creator_node_id"],
            )
            self.assertEqual(
                json.loads((directory / "receipt.json").read_text(encoding="utf-8"))[
                    "created_at"
                ],
                document["created_at"],
            )

    @staticmethod
    def _sample() -> dict[str, Any]:
        return copy.deepcopy(load_expert_manifest(SAMPLE))


if __name__ == "__main__":
    unittest.main()
