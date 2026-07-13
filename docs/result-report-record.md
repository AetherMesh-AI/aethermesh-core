# Local Result Report Record

A result report is the durable, local-first record for one completed, interrupted, or failed job attempt. It is not a consensus claim, a network trust decision, or an economic record. Its purpose is to preserve enough structured evidence for local comparison, replay checks, and future signing.

## Required top-level fields

Every version 6 record contains `schema_version`, `result_id`, `job_id`, `task_id`, `creator_node_id`, `executor_node_id`, `manifest_id`, `references`, `created_at`, `status`, `exit_code`, `started_at`, `finished_at`, `duration_ms`, `summary`, `error_summary`, `validation_status`, `validation_receipt_id`, `validator_node_id`, `failure_reasons`, `lineage`, and `contribution`.

Version 6 is the current durable job-result shape. Earlier records remain identifiable by their version but must be migrated before validation as version 6; they must never be silently reinterpreted as the current shape.

`creator_node_id` is retained even for failures. `manifest_id` and `references.manifest_hash` are matching SHA-256 content-addressed IDs. Timestamps are UTC and duration is derived from the execution timestamps.

## Outcome and validation status

Allowed outcome statuses are `succeeded`, `failed`, `timed_out`, `cancelled`, `validation_failed`, and `partially_completed`. `summary` is a short human-readable outcome description. `error_summary` is null only for `succeeded`; it supplements structured status and never replaces it.

Validation status is one of `pending`, `passed`, `failed`, `error`, or `not_run`. `pending` explicitly means local validation has not reached a final outcome; it is not a trust or consensus claim. The record identifies its local validation receipt or reserved local receipt ID by both `validation_receipt_id` and an entry in `references.validation_receipt_ids`.

Final local validation statuses (`passed`, `failed`, and `error`) require a canonical `result_hash`. Pending and not-run reports require `result_hash: null`, so an unvalidated report cannot appear to have final validation evidence. A receipt reference is local evidence only, including when it reserves a pending local receipt ID.

## References and lineage

`references.artifact_refs` and `references.log_refs` hold only relative local paths or `sha256:` content-addressed IDs. They never embed artifact or log content, absolute paths, parent traversal, URLs, or dashboard links. Empty lists are allowed when a job did not produce that evidence.

`lineage` preserves input and output manifest IDs, parent jobs and tasks, and artifact IDs. `contribution` repeats the creator, executor, and validator node IDs, and records `upstream_lineage_sources`; those sources must match `lineage.parent_job_ids`. This is attribution evidence only, not a reward calculation.

## Local validation expectations

The schema rejects missing or unknown fields, mismatched manifest or receipt references, invalid reference locations, incomplete attribution, invalid timestamps, and unsupported statuses. The canonical result hash includes stable report content and portable content-addressed evidence, but excludes runtime timestamps and machine-local artifact or log paths so relocated equivalent reports compare deterministically.
