# Phase 1 Job Failure Schema

`aethermesh_core.job_failure_schema.validate_job_failure_document` defines the strict, local-first version-1 `job_failure` record. It records an observed failure and supporting local evidence; it is not a network consensus result or proof of accepted contribution.

## Record contract

Every top-level field is required. `task_id` and `references.output_manifest_hash` may be `null` when no task or output exists.

| Field | Rules and purpose |
| --- | --- |
| `schema_version` | Integer `1`. |
| `failure_id`, `job_id`, `task_id` | Stable local references; `task_id` is nullable. |
| `creator_node_id`, `executing_node_id` | Preserve job creator and attempted executor attribution. |
| `observed_at` | UTC timestamp in `YYYY-MM-DDTHH:MM:SS.mmmZ` form. |
| `failure_type` | One of `task_crash`, `validation_failure`, `timeout`, `manifest_mismatch`, `contribution_rejected`, `missing_input`, or `environment_failure`. |
| `failure_stage` | One of `input`, `execution`, `output`, `validation`, or `attribution`. |
| `retryable`, `severity`, `human_summary` | Explicit retry decision, `warning`/`error`/`critical` severity, and bounded operator-safe summary. |
| `details` | Required nullable slots for `exit_code`, `signal`, `timeout_ms`, `validation_error_code`, `missing_input_id`, `manifest_mismatch`, `receipt_mismatch`, and `environment_issue_code`. The field matching the failure type is required (a crash may use exit code or signal; validation may use error code or receipt mismatch). Values are codes or references, never payload contents. |
| `references` | Required job/input manifest hashes, nullable output manifest hash, and arrays of validation receipt IDs, lineage parent IDs, and attribution record IDs. |
| `attribution` | Attempted contributor must equal the executing node. Records claimed work unit, non-negative accepted amount, and nullable rejection reason. Failed or rejected work normally has accepted amount `0`; it must never be inferred as accepted merely because it was attempted. |
| `evidence` | Arrays of repository-relative/local-runtime log paths, content hashes, validation command references, and observed timestamps. At least one evidence reference is required, timestamps are non-empty, and they include `observed_at`. |

Nested objects use exact fields so accidental raw payload or log fields are rejected. Empty reference arrays mean known-empty, not unknown.

## Evidence and redaction rules

Failure records contain references, hashes, bounded summaries, and machine-readable error codes only. Producers must:

- never store secrets, private keys, credentials, authorization headers, environment-variable values, or sensitive input/output payload contents;
- redact sensitive values before hashing referenced evidence and retain the redacted evidence only in an access-controlled local runtime location;
- use repository-relative or configured local-runtime paths, never host-specific absolute paths;
- keep validation commands in separately defined command records and store only their stable reference here; and
- replace sensitive error text with a safe code and operator summary.

The exact-field validator rejects ad hoc fields such as `raw_log`, `stderr`, `payload`, or `command`, preventing those common leak paths from becoming part of the contract. It cannot determine whether a permitted summary itself contains a secret, so producers remain responsible for redaction before validation.

## Examples and verification

`examples/job-failures/phase-1-examples.json` contains task-crash, validation-failure, timeout, manifest-mismatch, and rejected-contribution records. Tests validate each record, required identity/type/time/evidence fields, cross-links, attribution invariants, and rejection of raw evidence fields.
