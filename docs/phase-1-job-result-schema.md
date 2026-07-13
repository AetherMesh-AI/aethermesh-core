# Phase 1 Job Result Schema

`aethermesh_core.job_result_schema.validate_job_result_document` defines the local-only version-7 record emitted after a job has executed. It is an audit record for the runnable prototype, not a peer protocol, consensus claim, dashboard model, or reward ledger. The existing in-memory `JobResult` runner value remains intentionally small; this record is its durable provenance contract.

Version 7 supersedes version 6 by adding the explicit `pending` validation state and requiring `result_hash` to remain null for pending or not-run validation. Existing version 6 records are not version 7 records and must not be silently reinterpreted; migrate them explicitly before passing them to the version 7 validator.

## Required record fields

| Field | Source | Purpose |
| --- | --- | --- |
| `schema_version` | locally generated | Fixed integer `7`. |
| `result_hash` | canonical result payload | Required field. It is `null` while validation is `pending` or `not_run`; final local validation outcomes require a 64-character lowercase SHA-256 digest, which schema validation recomputes to reject stale values. |
| `result_id`, `job_id`, `task_id` | locally generated / referenced | Stable result, job, and task references. |
| `capability` | accepted manifest | Required machine-readable capability identifier (for example, `work.echo`), copied from the accepted manifest rather than worker output. |
| `creator_node_id`, `executor_node_id` | referenced | Job creator and node that executed local work. |
| `manifest_id`, `references` | derived from manifest and evidence | The content-addressed manifest ID plus bounded local artifact, log, and validation-receipt references. |
| `created_at`, `started_at`, `finished_at`, `reported_at`, `duration_ms` | locally generated / derived | UTC ISO 8601 timestamps with microsecond precision. `created_at` is the local submission time, `started_at` and `finished_at` bound execution, and `reported_at` is generated immediately before the durable report is written. They must be ordered; duration must equal the execution interval. Local clock values support audit ordering only and are not trust proof. |
| `status`, `exit_code`, `summary`, `error_summary` | locally generated | A supported terminal outcome, a process-style integer exit code, and bounded operator-safe outcome/error summaries. |
| `validation_status`, `validation_receipt_id`, `validator_node_id` | referenced | `pending`, `passed`, `failed`, `error`, or `not_run`, plus a required local receipt or reserved receipt ID and validator reference. `pending` is explicitly non-final local evidence, not a trust claim. |
| `failure_reasons` | locally generated | Separate nullable `execution`, `validation`, `malformed_input`, and `missing_artifact` reasons. |
| `lineage` | derived from manifests | Required arrays for input/output manifest IDs, parent job/task IDs, and deterministic artifact IDs. Empty arrays express a root result or no output. |
| `contribution` | locally generated | Repeats creator, executor, and validator IDs and preserves declared upstream lineage sources; `local_operator_id` is optional (`null` when unavailable). It records attribution only and has no reward, credit, or token meaning. |

Every top-level field is required. Nested reference, lineage, contribution, and failure-reason fields are required too, even when their values are empty arrays or `null`; this makes absent evidence distinguishable from known-empty evidence. IDs are non-empty, whitespace-free local references. Timestamps use `YYYY-MM-DDTHH:MM:SS.ffffffZ` UTC ISO 8601 form.

## Examples and validation

`examples/job-results/local-echo-success.json` is a validated successful result. `examples/job-results/local-echo-failed.json` demonstrates a failed execution with separate validation and missing-artifact reasons. `examples/job-results/local-echo-pending-validation.json` demonstrates an executed result with a reserved local receipt ID and explicitly pending validation. `tests/test_job_result_schema.py` validates these examples, rejects omission of attribution, lineage, manifest, reference, error, and validation evidence, and rejects invalid statuses, identifiers, and non-local artifact references.

The schema deliberately records local provenance only. A validation receipt is local evidence rather than distributed consensus, and the contribution block does not calculate rewards or tokenomics.

## Result hash behavior

`aethermesh_core.result_hash.canonical_result_document_hash` creates the Phase 1 durable result hash only after execution and a local validation receipt have reached `passed`, `failed`, or `error`; `pending` and `not_run` records retain `result_hash: null` and are intentionally not hashable. The sole supported algorithm is `sha256`. Store `result_hash_manifest(document)` beside the task manifest, result record, validation receipt, lineage references, and contribution identity metadata. Its explicit format is `{ "algorithm": "sha256", "result_hash": "<64 lowercase hex characters>" }`.

The UTF-8 hash payload uses compact JSON with lexicographically sorted object keys. It includes schema/result/job/task IDs and capability; creator and executor node IDs; the immutable `manifest_id` reference; inline output content or a referenced payload digest (never its machine-local storage path); portable content-addressed evidence and validation receipt IDs from `references`; result content (`status`, `exit_code`, `summary`, `error_summary`, and `failure_reasons`); validation status, receipt ID, and validator ID; full lineage (including parent task IDs); and contribution attribution. It intentionally excludes `result_hash` itself, lifecycle timestamps (`created_at`, `started_at`, `finished_at`, `reported_at`), `duration_ms`, machine-local artifact and log paths, runtime state, and display formatting. Array order remains meaningful provenance order.

Failed and errored artifacts remain hashable when they have this structured record and receipt. Re-running the same canonical inputs and result content yields the same hash. A validation receipt must store that exact value in `result_hash`; `validate_validation_receipt_result_hash` checks the link locally.
