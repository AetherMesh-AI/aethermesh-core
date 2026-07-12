# Phase 1 Job Result Schema

`aethermesh_core.job_result_schema.validate_job_result_document` defines the local-only version-1 record emitted after a job has executed. It is an audit record for the runnable prototype, not a peer protocol, consensus claim, dashboard model, or reward ledger. The existing in-memory `JobResult` runner value remains intentionally small; this record is its durable provenance contract.

## Required record fields

| Field | Source | Purpose |
| --- | --- | --- |
| `schema_version` | locally generated | Fixed integer `1`. |
| `result_id`, `job_id`, `task_id` | locally generated / referenced | Stable result, job, and task references. |
| `creator_node_id`, `executor_node_id` | referenced | Job creator and node that executed local work. |
| `manifest_id` | derived from manifest | The manifest governing this execution. |
| `created_at`, `started_at`, `finished_at`, `duration_ms` | locally generated / derived | UTC timestamps with millisecond precision; duration must equal the timestamp interval. |
| `status`, `exit_code`, `summary` | locally generated | `succeeded` or `failed`, a process-style integer exit code, and a bounded (512-character) operator-safe summary. |
| `validation_status`, `validation_receipt_id`, `validator_node_id` | referenced | `passed`, `failed`, or `not_run`, plus required local receipt and validator references. |
| `failure_reasons` | locally generated | Separate nullable `execution`, `validation`, `malformed_input`, and `missing_artifact` reasons. |
| `lineage` | derived from manifests | Required arrays for input/output manifest IDs, parent job/task IDs, and deterministic artifact IDs. Empty arrays express a root result or no output. |
| `contribution` | locally generated | `attribution_node_id` must equal `executor_node_id`; `local_operator_id` is optional (`null` when unavailable). It records attribution only and has no reward, credit, or token meaning. |

Every top-level field is required. Nested lineage and failure-reason fields are required too, even when their values are empty arrays or `null`; this makes absent evidence distinguishable from known-empty evidence. IDs are non-empty, whitespace-free local references. Timestamps use `YYYY-MM-DDTHH:MM:SS.mmmZ` form.

## Examples and validation

`examples/job-results/local-echo-success.json` is a validated successful result. `examples/job-results/local-echo-failed.json` demonstrates a failed execution with separate validation and missing-artifact reasons. `tests/test_job_result_schema.py` validates both, rejects omission of attribution, lineage, manifest, and validation evidence, and rejects invalid statuses and identifiers.

The schema deliberately records local provenance only. A validation receipt is local evidence rather than distributed consensus, and the contribution block does not calculate rewards or tokenomics.
