import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_phase1_api_schema.py"
CONTRACT = ROOT / "docs" / "phase-1-local-api-schemas.json"


class Phase1ApiSchemaTests(unittest.TestCase):
    def test_documented_examples_and_published_routes_validate_with_receipt(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            receipt_path = Path(temp_dir) / "schema-validation-receipt.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--contract",
                    str(CONTRACT),
                    "--receipt",
                    str(receipt_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(result.stdout), receipt)
        self.assertEqual(receipt["receipt_kind"], "phase_1_local_api_schema_validation")
        self.assertEqual(receipt["result"], "passed")
        self.assertGreater(receipt["example_count"], 0)
        self.assertGreater(receipt["published_route_count"], 0)

    def test_schema_validator_rejects_missing_required_creator_attribution(
        self,
    ) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        example = next(
            item
            for item in contract["examples"]
            if item["schema"] == "LocalValidationReceipt"
        )
        del example["payload"]["contribution_attribution"]["creator_node_id"]
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_contract = Path(temp_dir) / "invalid-contract.json"
            invalid_contract.write_text(json.dumps(contract), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--contract", str(invalid_contract)],
                capture_output=True,
                text=True,
                cwd=ROOT,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "contribution_attribution.creator_node_id is required", result.stderr
        )


if __name__ == "__main__":
    unittest.main()
