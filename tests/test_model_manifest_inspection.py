import asyncio
import json
import tempfile
import unittest
from pathlib import Path

import httpx

from aethermesh_core.api import create_app
from aethermesh_core.runtime_service import NodeRuntimeService


class ModelManifestInspectionTests(unittest.TestCase):
    def test_empty_endpoint_is_honest_and_local_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)

            async def fetch() -> httpx.Response:
                transport = httpx.ASGITransport(app=create_app(service))
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    return await client.get("/api/model-manifests")

            response = asyncio.run(fetch())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                {
                    "schema_version": 1,
                    "network_mode": "local-only-no-p2p",
                    "manifest_count": 0,
                    "manifests": [],
                    "note": "Local inspection only; validation status is not network consensus.",
                },
            )

    def test_valid_manifest_is_redacted_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            directory = home / "data" / "model-manifests"
            directory.mkdir(parents=True)
            path = directory / "coder-v2.json"
            document = {
                "manifest_id": "expert-coder-v2",
                "version": "2.0.0",
                "expert_type": "coding",
                "capability_tags": ["python", "tests"],
                "artifact_ref": "models/coder-v2.gguf",
                "creator_node_id": "node-creator-a",
                "timestamps": {"created_at": 100, "updated_at": 200},
                "validation": {
                    "status": "passed",
                    "receipt_refs": ["receipts/coder-v2.json"],
                },
                "lineage": {"parent_manifest_ids": ["expert-coder-v1"]},
                "contribution_attribution": {
                    "creator_node_id": "node-creator-a",
                    "contributor_node_ids": ["node-helper-b"],
                    "source": "local-import",
                    "reward_estimate": 999,
                },
                "api_token": "must-not-leak",
                "private_key": "must-not-leak",
            }
            path.write_text(json.dumps(document), encoding="utf-8")
            before = path.read_bytes()

            response = NodeRuntimeService.from_home(home).inspect_model_manifests()
            summary = response["manifests"][0]

            self.assertEqual(response["manifest_count"], 1)
            self.assertEqual(summary["manifest_id"], "expert-coder-v2")
            self.assertEqual(summary["creator_node_id"], "node-creator-a")
            self.assertEqual(summary["validation"]["status"], "passed")
            self.assertEqual(
                summary["lineage"]["parent_manifest_ids"], ["expert-coder-v1"]
            )
            self.assertEqual(
                summary["contribution_attribution"]["contributor_node_ids"],
                ["node-helper-b"],
            )
            self.assertEqual(summary["inspection_status"], "ok")
            self.assertNotIn("api_token", json.dumps(response))
            self.assertNotIn("private_key", json.dumps(response))
            self.assertNotIn("reward", json.dumps(response))
            self.assertNotIn("consensus", summary)
            self.assertEqual(path.read_bytes(), before)

    def test_malformed_and_invalid_manifests_degrade_without_leaking_paths(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir) / "data" / "model-manifests"
            directory.mkdir(parents=True)
            (directory / "broken.json").write_text("{bad", encoding="utf-8")
            (directory / "invalid.json").write_text(
                json.dumps(
                    {
                        "manifest_id": "",
                        "version": True,
                        "expert_type": None,
                        "capability_tags": "python",
                        "artifact_ref": "",
                        "creator_node_id": 4,
                        "timestamps": [],
                        "validation": [],
                        "lineage": [],
                        "contribution_attribution": [],
                    }
                ),
                encoding="utf-8",
            )
            (directory / "unsafe.json").write_text(
                json.dumps(
                    {
                        "manifest_id": "unsafe",
                        "version": 1,
                        "expert_type": "test",
                        "artifact_ref": "secret.env",
                        "creator_node_id": "node-a",
                        "validation": {
                            "status": "trusted-by-network",
                            "receipt_refs": ["../receipt.json"],
                        },
                        "lineage": {"parent_manifest_ids": [1]},
                    }
                ),
                encoding="utf-8",
            )

            response = NodeRuntimeService.from_home(temp_dir).inspect_model_manifests()

            self.assertEqual(response["manifest_count"], 3)
            self.assertTrue(
                all(
                    item["inspection_status"] == "degraded"
                    for item in response["manifests"]
                )
            )
            rendered = json.dumps(response)
            self.assertIn("model manifest JSON is malformed", rendered)
            self.assertIn(
                "artifact_ref must be a safe local relative reference", rendered
            )
            self.assertNotIn(str(Path(temp_dir)), rendered)
            unsafe = next(
                item
                for item in response["manifests"]
                if item.get("manifest_id") == "unsafe"
            )
            self.assertEqual(unsafe["validation"]["status"], "unknown")
            self.assertEqual(unsafe["validation"]["receipt_refs"], [])
            self.assertEqual(unsafe["lineage"]["parent_manifest_ids"], [])


if __name__ == "__main__":
    unittest.main()
