import json
import re
import tempfile
import unittest
from pathlib import Path
from typing import Any

from aethermesh_core.runtime_service import NodeRuntimeService


CONTRACT_PATH = Path("docs/phase-1-api-schema-contract.md")
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def _documented_examples() -> list[dict[str, Any]]:
    document = CONTRACT_PATH.read_text(encoding="utf-8")
    return [json.loads(block) for block in JSON_BLOCK.findall(document)]


class Phase1ApiSchemaContractTests(unittest.TestCase):
    def test_documented_examples_are_valid_json_and_match_local_contract(self) -> None:
        examples = _documented_examples()
        submission = next(example for example in examples if "job_type" in example)
        receipt_example = next(
            example for example in examples if "receipt_id" in example
        )
        contribution_example = next(
            example for example in examples if "accepted_work_count" in example
        )
        required_request_fields = {
            "job_type",
            "payload",
            "creator_node_id",
            "requested_validation_mode",
            "lineage_parent_refs",
            "attribution_metadata",
        }
        self.assertEqual(required_request_fields, set(submission))
        self.assertIsInstance(submission["payload"], dict)
        self.assertIsInstance(submission["lineage_parent_refs"], list)
        self.assertIsInstance(submission["attribution_metadata"], dict)
        self.assertEqual(receipt_example["schema_version"], 1)
        self.assertEqual(receipt_example["validation"]["valid"], True)
        self.assertEqual(contribution_example["items"], [])

        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(temp_dir)
            accepted = service.submit_local_job(submission)
            self.assertEqual(accepted["status"], "accepted_pending_execution")
            self.assertIn("job_id", accepted)
            self.assertIn("manifest_ref", accepted)

            completed = service.execute_submitted_local_job(
                accepted["job_id"], "worker-local-a"
            )
            receipt = service.get_local_validation_receipt(work_id=accepted["job_id"])
            contribution = service.contribution_summary()

        for field in (
            "schema_version",
            "receipt_id",
            "work_id",
            "creator_node_id",
            "manifest_ref",
            "validation",
            "validator_identity",
            "lineage_parent_ids",
            "contribution_attribution",
            "evidence",
        ):
            self.assertIn(field, receipt)
        self.assertEqual(receipt["schema_version"], receipt_example["schema_version"])
        self.assertEqual(receipt["creator_node_id"], submission["creator_node_id"])
        self.assertEqual(receipt["manifest_ref"], accepted["manifest_ref"])
        self.assertEqual(
            receipt["validation"]["valid"], completed["validation"]["passed"]
        )
        self.assertEqual(
            contribution["network_mode"], contribution_example["network_mode"]
        )
        self.assertEqual(contribution["summary_status"], "recorded")
        self.assertEqual(contribution["accepted_work_count"], 1)
        item = contribution["items"][0]
        for field in (
            "creator_node_id",
            "manifest_ref",
            "validation_receipt_ref",
            "lineage_links",
        ):
            self.assertIn(field, item)
