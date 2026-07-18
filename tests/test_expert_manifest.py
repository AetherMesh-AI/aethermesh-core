import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from aethermesh_core.expert_manifest import (
    ExpertManifestError,
    RECEIPT_VERSION,
    expert_is_usable,
    load_expert_manifest,
    validate_expert_manifest,
)


ROOT = Path(__file__).parents[1]
SAMPLE = ROOT / "examples/model-experts/echo-expert-v0/manifest.json"


class ExpertManifestTests(unittest.TestCase):
    def test_sample_parses_and_unvalidated_manifest_is_not_usable(self) -> None:
        document = load_expert_manifest(SAMPLE)

        self.assertEqual(document["expert_id"], "local-echo-fixture-v0")
        self.assertEqual(document["validation"]["receipt_path"], None)
        self.assertFalse(expert_is_usable(SAMPLE))

    def test_copy_preserves_lineage_and_attribution(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            copied = Path(temp_dir) / "manifest.json"
            shutil.copyfile(SAMPLE, copied)

            original = load_expert_manifest(SAMPLE)
            handoff = load_expert_manifest(copied)

        self.assertEqual(handoff["lineage"], original["lineage"])
        self.assertEqual(
            handoff["contribution_attribution"], original["contribution_attribution"]
        )

    def test_required_fields_and_malformed_json_fail_clearly(self) -> None:
        with self.assertRaisesRegex(ExpertManifestError, "must contain exactly"):
            validate_expert_manifest([])
        document = self._sample()
        document.pop("creator_node_id")
        with self.assertRaisesRegex(
            ExpertManifestError, "expert manifest must contain exactly"
        ):
            validate_expert_manifest(document)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaisesRegex(ExpertManifestError, "JSON is malformed"):
                load_expert_manifest(path)

    def test_schema_rejects_invalid_required_values(self) -> None:
        cases = [
            ("manifest_version", "other", "manifest_version must be"),
            ("expert_id", "", "expert_id must be"),
            ("created_at", "yesterday", "created_at must be"),
            ("supported_task_categories", [], "supported_task_categories must be"),
            ("runtime_requirements", [""], "runtime_requirements must be"),
        ]
        for field, value, message in cases:
            with self.subTest(field=field):
                document = self._sample()
                document[field] = value
                with self.assertRaisesRegex(ExpertManifestError, message):
                    validate_expert_manifest(document)

    def test_schema_rejects_incomplete_or_unsafe_nested_evidence(self) -> None:
        cases = [
            (
                "artifact",
                {"reference": "../artifact", "sha256": "sha256:" + "a" * 64},
                "artifact.reference",
            ),
            ("lineage", {}, "lineage must contain exactly"),
            ("validation", {"status": "unknown"}, "validation must contain exactly"),
            (
                "contribution_attribution",
                {},
                "contribution_attribution must contain exactly",
            ),
        ]
        for field, value, message in cases:
            with self.subTest(field=field):
                document = self._sample()
                document[field] = value
                with self.assertRaisesRegex(ExpertManifestError, message):
                    validate_expert_manifest(document)
        document = self._sample()
        document["validation"].update(
            {
                "status": "passed",
                "test_command": "test",
                "expected_inputs_ref": "input.json",
            }
        )
        with self.assertRaisesRegex(
            ExpertManifestError, "passed validation requires complete"
        ):
            validate_expert_manifest(document)

        document = self._sample()
        document["lineage"]["derived_artifact_refs"] = None
        with self.assertRaisesRegex(
            ExpertManifestError, "derived_artifact_refs must be"
        ):
            validate_expert_manifest(document)

    def test_validation_evidence_matches_contribution_attribution(self) -> None:
        document = self._sample()
        document["validation"]["validator_node_id"] = "node-validator"
        with self.assertRaisesRegex(
            ExpertManifestError, "validator_node_id must match"
        ):
            validate_expert_manifest(document)

        document = self._sample()
        document["validation"]["receipt_path"] = "receipt.json"
        with self.assertRaisesRegex(ExpertManifestError, "must appear in"):
            validate_expert_manifest(document)

    def test_nested_collections_and_status_fail_with_manifest_error(self) -> None:
        document = self._sample()
        document["validation"]["status"] = []
        with self.assertRaisesRegex(ExpertManifestError, "validation.status must be"):
            validate_expert_manifest(document)

        document = self._sample()
        document["contribution_attribution"]["receipt_refs"] = "abc"
        with self.assertRaisesRegex(
            ExpertManifestError, "contribution_attribution.receipt_refs must be"
        ):
            validate_expert_manifest(document)

    def test_usable_requires_matching_artifact_and_real_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            artifact = directory / "artifact.txt"
            artifact.write_text("artifact", encoding="utf-8")
            receipt = directory / "receipt.json"
            document = self._sample()
            document["artifact"]["sha256"] = (
                "sha256:cfb2e16a101a0000000000000000000000000000000000000000000000000000"
            )
            validation = document["validation"]
            validation.update(
                {
                    "status": "passed",
                    "test_command": "python -m unittest",
                    "expected_inputs_ref": "input.json",
                    "receipt_path": "receipt.json",
                    "last_validated_at": "2026-07-18T00:00:01Z",
                    "validator_node_id": "node-validator",
                }
            )
            document["lineage"]["derived_artifact_refs"] = ["artifact.txt"]
            document["contribution_attribution"].update(
                {
                    "modifier_node_ids": ["node-modifier"],
                    "validator_node_id": "node-validator",
                    "receipt_refs": ["receipt.json"],
                }
            )
            path = directory / "manifest.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertFalse(expert_is_usable(path))
            document["artifact"]["sha256"] = self._hash(artifact)
            path.write_text(json.dumps(document), encoding="utf-8")
            receipt_document = {
                "receipt_version": RECEIPT_VERSION,
                "expert_id": document["expert_id"],
                "artifact_sha256": document["artifact"]["sha256"],
                "validated_at": validation["last_validated_at"],
                "validator_node_id": validation["validator_node_id"],
                "status": "passed",
            }
            receipt.write_text(json.dumps(receipt_document), encoding="utf-8")
            with patch(
                "aethermesh_core.expert_manifest._sha256",
                side_effect=OSError("read failed"),
            ):
                self.assertFalse(expert_is_usable(path))
            self.assertTrue(expert_is_usable(path))

            receipt.write_text("not JSON", encoding="utf-8")
            self.assertFalse(expert_is_usable(path))
            receipt.write_text("{}", encoding="utf-8")
            self.assertFalse(expert_is_usable(path))
            receipt_document["artifact_sha256"] = "sha256:" + "0" * 64
            receipt.write_text(json.dumps(receipt_document), encoding="utf-8")
            self.assertFalse(expert_is_usable(path))
            receipt_document["artifact_sha256"] = document["artifact"]["sha256"]
            receipt.write_text(json.dumps(receipt_document), encoding="utf-8")

            outside = directory.parent / "outside.txt"
            outside.write_text("artifact", encoding="utf-8")
            artifact.unlink()
            artifact.symlink_to(outside)
            self.assertFalse(expert_is_usable(path))

    def test_read_error_does_not_leak_local_path(self) -> None:
        missing = Path(tempfile.gettempdir()) / "private-manifest-location.json"
        with self.assertRaisesRegex(
            ExpertManifestError, "could not read expert manifest"
        ) as raised:
            load_expert_manifest(missing)
        self.assertNotIn(str(missing), str(raised.exception))

    @staticmethod
    def _sample() -> dict[str, Any]:
        return copy.deepcopy(load_expert_manifest(SAMPLE))

    @staticmethod
    def _hash(path: Path) -> str:
        import hashlib

        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    unittest.main()
