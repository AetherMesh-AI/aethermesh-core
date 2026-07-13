import copy
import json
import unittest
from pathlib import Path

from aethermesh_core.result_hash import validate_validation_receipt_result_hash
from aethermesh_core.validation_receipt_schema import (
    ValidationReceiptSchemaError,
    canonical_validation_receipt_hash,
    validation_receipt_id,
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
        self.assertEqual(
            self.failing["lineage"]["prior_receipt_ids"],
            [self.passing["receipt_id"]],
        )
        validate_validation_receipt_result_hash(
            self.passing, self.passing["result_hash"]
        )

    def test_required_fields_and_unknown_fields_are_rejected(self) -> None:
        missing = copy.deepcopy(self.passing)
        missing.pop("job_id")
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "missing: job_id"):
            validate_validation_receipt_document(missing)

        blank = copy.deepcopy(self.passing)
        blank["job_id"] = ""
        with self.assertRaisesRegex(
            ValidationReceiptSchemaError, "job_id must be a non-empty identifier"
        ):
            validate_validation_receipt_document(blank)

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
        self.assertEqual(first["receipt_id"], validation_receipt_id(first["work_id"]))
        self.assertEqual(
            canonical_validation_receipt_hash(first),
            canonical_validation_receipt_hash(second),
        )
        self.assertEqual(
            first["receipt_hash"], canonical_validation_receipt_hash(first)
        )

    def test_receipt_id_must_be_derived_from_work_id(self) -> None:
        receipt = copy.deepcopy(self.passing)
        receipt["receipt_id"] = "local-validation-receipt-unrelated-work"
        receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "match its work_id"):
            validate_validation_receipt_document(receipt)

    def test_job_id_must_match_work_id(self) -> None:
        receipt = copy.deepcopy(self.passing)
        receipt["job_id"] = "unrelated-job"
        receipt["receipt_hash"] = canonical_validation_receipt_hash(receipt)
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "match its work_id"):
            validate_validation_receipt_document(receipt)

    def test_hash_mismatch_is_rejected(self) -> None:
        receipt = copy.deepcopy(self.passing)
        receipt["evidence"]["reason"] = "changed after hashing"
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "does not match"):
            validate_validation_receipt_document(receipt)

    def test_types_hashes_and_json_compatibility_are_strict(self) -> None:
        for field, value in (("schema_version", 1.0), ("validation_status", [])):
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.passing)
                receipt[field] = value
                with self.assertRaises(ValidationReceiptSchemaError):
                    validate_validation_receipt_document(receipt)

        receipt = copy.deepcopy(self.passing)
        receipt["lineage"]["input_hashes"] = ["sha256:not-a-digest"]
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "content-addressed"):
            validate_validation_receipt_document(receipt)

        receipt = copy.deepcopy(self.passing)
        receipt["result_hash"] = "sha256:not-a-digest"
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "SHA-256 digest"):
            validate_validation_receipt_document(receipt)

        receipt = copy.deepcopy(self.passing)
        receipt["not_json"] = {float("nan")}
        with self.assertRaisesRegex(ValidationReceiptSchemaError, "JSON-compatible"):
            canonical_validation_receipt_hash(receipt)

    def test_local_references_cannot_leak_machine_paths(self) -> None:
        cases = (
            ("lineage", "source_manifest_refs", "/Users/example/private.json"),
            ("contribution", "contribution_manifest_ref", "../private.json"),
            ("evidence", "log_path", "C:\\Users\\example\\private.log"),
            ("evidence", "artifact_path", "https://example.test/result.json"),
        )
        for block, field, value in cases:
            with self.subTest(block=block, field=field):
                receipt = copy.deepcopy(self.passing)
                receipt[block][field] = [value] if block == "lineage" else value
                with self.assertRaisesRegex(ValidationReceiptSchemaError, "relative"):
                    validate_validation_receipt_document(receipt)

    def test_reason_is_required_validation_evidence(self) -> None:
        for value in (None, ""):
            with self.subTest(value=value):
                receipt = copy.deepcopy(self.passing)
                receipt["evidence"]["reason"] = value
                with self.assertRaisesRegex(ValidationReceiptSchemaError, "non-empty"):
                    validate_validation_receipt_document(receipt)

    def test_lineage_and_attribution_ids_reject_whitespace(self) -> None:
        nullable = copy.deepcopy(self.passing)
        nullable["contribution"]["submitter_id"] = None
        nullable["receipt_hash"] = canonical_validation_receipt_hash(nullable)
        self.assertIs(validate_validation_receipt_document(nullable), nullable)

        cases = (
            ("lineage", "parent_work_ids", ["not an id"]),
            ("lineage", "prior_receipt_ids", ["receipt\nleak"]),
            ("contribution", "submitter_id", "/Users/example/private id"),
            ("contribution", "claimed_role", "validator\nsecret"),
        )
        for block, field, value in cases:
            with self.subTest(block=block, field=field):
                receipt = copy.deepcopy(self.passing)
                receipt[block][field] = value
                with self.assertRaisesRegex(ValidationReceiptSchemaError, "identifier"):
                    validate_validation_receipt_document(receipt)
