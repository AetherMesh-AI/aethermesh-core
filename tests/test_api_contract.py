import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


class ApiContractValidationTests(unittest.TestCase):
    def test_contract_examples_and_generated_openapi_routes_validate(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        environment = {
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
        }
        completed = subprocess.run(
            [sys.executable, "scripts/validate_api_contract.py"],
            cwd=repository,
            env=environment,
            capture_output=True,
            check=True,
            text=True,
        )
        receipt = json.loads(completed.stdout)
        self.assertEqual(receipt["result"], "passed")
        self.assertEqual(receipt["openapi_route_match"], "passed")
        self.assertEqual(receipt["examples"]["job_submission"], "passed")
        self.assertEqual(
            receipt["missing_required_field_checks"][
                "validation_receipt_lookup:contribution_attribution"
            ],
            "rejected",
        )
