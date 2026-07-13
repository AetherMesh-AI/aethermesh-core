import copy
import json
import unittest
from pathlib import Path

from aethermesh_core.validation_receipt_schema import (
    ValidationReceiptSchemaError,
    canonical_validation_receipt_hash,
    validate_validation_receipt_document,
)


class ValidationReceiptSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        examples = root / "examples" / "validation-receipts"
        self.passing = json.loads(
            (examples / "local-echo-pass.json").read_text("utf-8")
        )
        self.failing = json.loads(
            (examples / "local-echo-fail.json").read_text("utf-8")
        )

    def test_passing_and_failing_examples_validate(self) -> None:
        self.assertIs(validate_validation_receipt_document(self.passing), self.passing)
        self.assertIs(validate_validation_receipt_document(self.failing), self.failing)
        self.assertEqual(self.passing["validation_status"], "pass")
        self.assertEqual(self.failing["validation_status"], "fail")

    def test_required_fields_and_unknown_fields_are_rejected(self) -> None:
        missing = copy.deepcopy(self.passing)
        missing.pop("validator_id")
        with self.assertRaisesRegex(
            ValidationReceiptSchemaError, "missing: validator_id"
        ):
            validate_validation_receipt_document(missing)

        unknown = copy.deepcopy(self.passing)
        unknown["unreviewed_critical_field"] = "not silently accepted"
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "unsupported fields"):
            validate_validation_receipt_document(unknown)

    def test_all_documented_validation_states_are_allowed(self) -> None:
        for state in ("pass", "fail", "error", "skipped"):
            with self.subTest(state=state):
                receipt = copy.deepcopy(self.passing)
                receipt["validation_status"] = state
                receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
                self.assertIs(validate_validation_receipt_document(receipt), receipt)

    def test_identical_local_evidence_has_stable_id_and_hash(self) -> None:
        first = copy.deepcopy(self.passing)
        second = copy.deepcopy(self.passing)
        second["created_at"] = "2026-07-13T12:01:00.000000Z"
        self.assertEqual(first["receipt_id"], second["receipt_id"])
        self.assertEqual(
            canonical_validation_receipt_hash(first),
            canonical_validation_receipt_hash(second),
        )
        self.assertEqual(
            first["receipt_hash"], canonical_validation_receipt_hash(first)
        )

    def test_hash_mismatch_is_rejected(self) -> None:
        receipt = copy.deepcopy(self.passing)
        receipt["evidence"]["reason"] = "changed after hashing"
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "does not match"):
            validate_validation_receipt_document(receipt)
