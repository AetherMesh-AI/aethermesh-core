# Phase 1 Job Failure Schema

`aethermesh_core.job_failure_schema.validate_job_failure_document` defines the local-only version-1 `job_failure` record. It records an observed failure and its provenance; it is not a network consensus result, accepted contribution, or reward decision.

## Record contract

Every record requires stable `failure_id` and `job_id` references, nullable `task_id`, creator and executing node IDs, and a millisecond UTC `observed_at`. Classification is explicit through `failure_type`, `failure_stage`, `retryable`, `severity`, and a bounded operator-safe `human_summary`.

`details` contains fixed nullable machine-readable slots for process exit code or signal, timeout, validation error, missing input, expected/observed manifest hashes, expected/observed receipt IDs, and execution-environment issue code. At least one detail must be present. This avoids an untestable summary-only failure.

`links` requires SHA-256 job and input manifest hashes, permits an output manifest hash only when output exists, and carries validation receipt IDs, lineage parent IDs, and attribution record IDs. These are references; the failure record does not embed manifests or receipts.

`attribution` records the attempted contributor, claimed work unit, non-negative accepted amount, and rejection reason. A zero accepted amount requires a reason. Attempted work is never inferred to be accepted merely because a failure record exists.

`evidence` requires at least one log reference with a safe repository-relative/local-relative path or a SHA-256 content hash. Validation command references may identify separately stored command definitions. Evidence has its own observed timestamp so the observation can be reproduced and ordered.

## Failure types and examples

Supported types are `task_crash`, `validation_failure`, `timeout`, `manifest_mismatch`, `rejected_contribution`, `missing_input`, `receipt_mismatch`, and `execution_environment`. Stages are `input`, `execution`, `validation`, and `attribution`; severities are `info`, `warning`, `error`, and `critical`.

Validated examples are under `examples/job-failures/` for task crash, validation failure, timeout, manifest mismatch, and rejected contribution. `tests/test_job_failure_schema.py` checks these examples, mandatory identity/evidence fields, provenance links, attribution safety, and redaction-oriented structural limits.

## Redaction and storage rules

Failure records must never contain secret values, private keys, credentials, authorization headers, environment dumps, or sensitive input/output payloads. The closed schema intentionally has no raw-log, command-text, environment, or payload fields. Store sanitized material separately and reference it by safe relative path and/or content hash. Validation commands are IDs, not shell command text. Operators must redact referenced logs before hashing or retaining them; a hash proves which sanitized evidence was observed but does not make unsafe content safe.

Records are local audit evidence. Receipt and manifest references do not imply independent validation, decentralization, or agreement by another node.
