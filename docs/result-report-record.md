# Local Result Report Record

A result report is the durable, local-first record for one completed, interrupted, or failed job attempt. It is not a consensus claim, a network trust decision, or an economic record. Its purpose is to preserve enough structured evidence for local comparison, replay checks, and future signing.

## Required top-level fields

Every version 9 record contains `schema_version`, `result_hash`, `result_id`, `job_id`, `task_id`, `capability`, `model_expert_id`, `creator_node_id`, `executor_node_id`, `manifest_id`, `output_payload`, `references`, `created_at`, `status`, `exit_code`, `started_at`, `finished_at`, `reported_at`, `duration_ms`, `summary`, `error_summary`, `validation_status`, `validation_receipt_id`, `validator_node_id`, `failure_reasons`, `lineage`, and `contribution`.

Version 9 supersedes version 8 by requiring `model_expert_id`. This is a stable, deterministic, non-secret, whitespace-free local identifier for the model, expert, or worker that produced the output; it is distinct from creator, executor, validator, and contributor node identities. Earlier records remain identifiable by their version but must be migrated before validation as version 9; they must never be silently reinterpreted as the current shape.

`creator_node_id` is retained even for failures. `manifest_id` and `references.manifest_hash` are matching SHA-256 content-addressed IDs. Timestamps are UTC and duration is derived from the execution timestamps.

## Outcome and validation status

Allowed outcome statuses are `succeeded`, `failed`, `timed_out`, `cancelled`, `validation_failed`, and `partially_completed`. `summary` is a short human-readable outcome description. `error_summary` is null only for `succeeded`; it supplements structured status and never replaces it.

Validation status is one of `pending`, `passed`, `failed`, `error`, or `not_run`. `pending` explicitly means local validation has not reached a final outcome; it is not a trust or consensus claim. The record identifies its local validation receipt or reserved local receipt ID by both `validation_receipt_id` and an entry in `references.validation_receipt_ids`.

Final local validation statuses (`passed`, `failed`, and `error`) require a canonical `result_hash`. Pending and not-run reports require `result_hash: null`, so an unvalidated report cannot appear to have final validation evidence. A receipt reference is local evidence only, including when it reserves a pending local receipt ID.

## References and lineage

`references.artifact_refs` and `references.log_refs` hold only relative local paths or `sha256:` content-addressed IDs. They never embed artifact or log content, absolute paths, parent traversal, URLs, or dashboard links. Empty lists are allowed when a job did not produce that evidence.

`lineage` preserves input and output manifest IDs, parent jobs and tasks, and artifact IDs. `contribution` repeats the creator, executor, and validator node IDs, and records `upstream_lineage_sources`; those sources must match `lineage.parent_job_ids`. This is attribution evidence only, not a reward calculation.

## Local storage and read path

The runtime creates each report once at `data/job-results/<job-id>.json` with an atomic, no-replace write. A repeated submission with the same job ID cannot replace an existing report. Local tooling can load and schema-check a report with `NodeRuntimeService.get_local_job_result(job_id)` or read it through `GET /api/jobs/{job_id}/result`; neither read path changes local state. Invalid job IDs receive the stable local API `400 INVALID_INPUT` envelope, and absent reports receive `404 RESULT_REPORT_NOT_FOUND`.

`POST /api/result-reports/preflight` and `NodeRuntimeService.preflight_local_result_report()` provide the local-only candidate boundary before validation. They require the version 9 schema plus an existing matching local manifest, creator, capability, model/expert ID, reserved receipt ID, and lineage. Candidate reports must remain `pending` or `not_run` with `result_hash: null`; preflight does not create a result record, receipt, contribution, or lineage state. A malformed candidate produces a bounded local `data/rejected-result-reports/` audit record containing its machine-readable reason code, a reason capped at 512 characters, processing timestamp, and original report (or a hash and bounded prefix when it exceeds 16 KiB).

`GET /api/result-reports` and `NodeRuntimeService.list_local_job_results()` provide a local-only, job-ID-sorted listing. The version 1 response is `{schema_version, total, result_reports}`. Each summary has `result_id`, `job_id`, `status`, `capability`, `timestamps`, `validation` (status, receipt ID, and receipt IDs), `manifest` (ID and hash), `lineage`, `creator_node_id`, `contribution`, and `result_hash`. It deliberately excludes `output_payload`, `summary`, `error_summary`, `failure_reasons`, artifact references, and log references; use the detail route only for a known local job ID when that fuller validated record is required.

## Local validation expectations

The schema rejects missing or unknown fields, mismatched manifest or receipt references, invalid reference locations, incomplete attribution, invalid timestamps, and unsupported statuses. The canonical result hash includes stable report content and portable content-addressed evidence, but excludes runtime timestamps and machine-local artifact or log paths so relocated equivalent reports compare deterministically.
