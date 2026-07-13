# Phase 1 Validation Receipt Schema

`aethermesh_core.validation_receipt_schema` defines a small JSON-only local validation receipt. It records local evidence for a completed validation. It is not a peer protocol, consensus proof, reward ledger, or production trust claim.

## Required fields

Every top-level field is required and unknown top-level fields are rejected. This strict rule prevents a reader from silently accepting an unreviewed critical field. Version 1 requires:

| Field | Meaning |
| --- | --- |
| `schema_version` | Fixed integer `1`. |
| `receipt_id` | Stable local receipt identifier. |
| `receipt_hash` | SHA-256 hash of the canonical stable receipt content. |
| `result_hash` | Exact lowercase SHA-256 digest of the durable job result being validated. |
| `created_at` | UTC ISO 8601 creation timestamp; audit ordering only. |
| `creator_node_id` | Node that created the submitted work. |
| `work_id` | Work item validated by the receipt. |
| `manifest_id` | Content-addressed source work manifest identifier. |
| `validation_status` | One of `pass`, `fail`, `error`, or `skipped`. |
| `validator_id` | Local validator or deterministic validator implementation identity. |
| `lineage` | Required lineage block described below. |
| `contribution` | Required local attribution block described below. |
| `evidence` | Required local validation evidence block described below. |

`pass` means the listed local check completed and met its expectation. `fail` means it completed but did not meet that expectation. `error` means validation could not complete reliably. `skipped` means it was deliberately not run. None is a network or consensus claim.

## Nested blocks and reserved nullable placeholders

All five `lineage` arrays are required and may be empty for root work: `parent_work_ids`, `source_manifest_refs`, `input_hashes`, `output_hashes`, and `prior_receipt_ids`. Manifest, input, and output hashes use lowercase `sha256:` content-addressed IDs with 64 hexadecimal digits. Source manifest references must be safe repository-relative local paths.

All `contribution` fields are required. `submitter_id`, `local_node_id`, `claimed_role`, and `contribution_manifest_ref` are nullable placeholders when the local input did not provide the corresponding attribution. Non-null identity and role values are whitespace-free identifiers. A non-null contribution manifest reference must be a safe repository-relative local path. These fields record a claim only; they do not calculate credit or rewards.

All `evidence` fields are required. `test_command`, `environment_summary`, `log_path`, and `artifact_path` are nullable when unavailable. `exit_code` is nullable when no command was run. `reason` is a required, non-empty deterministic local pass/fail/error/skip explanation. Paths are safe repository-relative local references, never URLs, home-relative references, parent traversals, or machine-absolute paths.

## Stable hash and replay expectation

Receipts are plain JSON and use compact UTF-8 JSON with sorted keys for `receipt_hash`. The hash deliberately excludes `created_at` and `receipt_hash`, so repeated local validation of identical work, result content, lineage, attribution, and evidence produces the same receipt hash even when audit timestamps differ. `result_hash` preserves the existing durable job-result link and is compatible with `validate_validation_receipt_result_hash`. `receipt_id` is supplied by the stable local work identity and must likewise repeat for the same work. Future replay code should validate the schema and recompute `receipt_hash` before using the evidence.

## Examples and verification

`examples/validation-receipts/local-echo-pass.json` and `examples/validation-receipts/local-echo-fail.json` are complete pass and fail examples. `tests/test_validation_receipt_schema.py` validates both examples, omission handling, strict unknown-field rejection, all allowed states, and stable ID/hash behavior across repeated local validation-shaped inputs.
