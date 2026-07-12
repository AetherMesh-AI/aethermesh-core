# Phase 1 Job Failure Schema

`aethermesh_core.job_failure_schema.validate_job_failure_document` defines the local-first version-1 `job_failure` record. It records an attributable observation, not network consensus, and does not grant contribution credit.

## Contract

Every record requires stable `failure_id` and `job_id` references, nullable `task_id`, creator and executing node IDs, and a millisecond UTC `observed_at`. Classification is explicit: `failure_type`, `failure_stage`, `retryable`, `severity`, and a bounded operator-safe `human_summary`.

`details` has fixed nullable fields for `exit_code`, `signal`, `timeout_ms`, `validation_error`, `missing_input`, `manifest_mismatch`, `receipt_mismatch`, and `environment_issue`; at least one must be populated. Supported initial failure types are task crash, validation failure, timeout, manifest mismatch, and contribution rejection.

`links` requires the governing job and input manifest hashes, permits a nullable output manifest hash, and always carries validation receipt and lineage-parent ID arrays. Empty arrays mean known-empty rather than unknown.

`attribution` identifies the attempted contributor and claimed work unit. `accepted_work_amount` is a non-negative local accounting quantity, not currency or a reward. Zero accepted work requires a rejection reason, preventing attempted work from silently becoming accepted contribution.

## Evidence and redaction

`evidence` requires observed timestamps and at least one repository-relative local log path, content hash, or validation-command reference. References are identifiers; paths must not be absolute or traverse parents.

Failure records must never contain log bodies, inputs, outputs, prompts, environment dumps, secrets, credentials, private keys, access tokens, or sensitive payload contents. Store only a safe relative path or content hash after placing sensitive material in access-controlled local storage. The validator rejects unknown fields, including embedded `log_contents` or payload fields. Summaries and detail strings must be manually redacted and bounded; they are descriptions, not storage for raw evidence.

## Examples and validation

`examples/job-failures/` contains validated task-crash, validation-failure, timeout, manifest-mismatch, and rejected-contribution records. `tests/test_job_failure_schema.py` validates all five, required fields and evidence, provenance links, attribution-safe rejection, and redaction-oriented structural rules.
