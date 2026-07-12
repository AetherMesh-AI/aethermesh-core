# Phase 1 API Schema Contract

Schema contract version: `1`. This is the stable, local-only companion to [the API boundary](phase-1-local-api-boundary.md). The boundary document indexes every localhost route and its behavior; this document fixes the versioned provenance payloads that can be persisted or exchanged between local process runs.

Compatibility rule: additive optional fields are allowed within schema version 1. Removing, renaming, or changing the meaning or type of a required field requires a new schema version, an updated example, and a migration note in this document. There are no prior versioned HTTP submission schemas to migrate; version 1 is the baseline.

## Route index

| Route | Request | Response contract |
| --- | --- | --- |
| `GET /health`, `/status`, `/api/status`, `/version`, `/node`, `/api/node`, `/peers`, `/api/peers`, `/api/jobs`, `/capabilities`, `/api/capabilities`, `/api/model-manifests`, `/api/package`, `/api/network`, `/logs`, `/api/logs`, `/api/events`, `/`, `/shutdown`, `/restart` | None, except local control signal posts | Current local status/control shape described in the API boundary; none writes provenance. |
| `POST /api/jobs` | Local Job Submission v1 | Local Job Submission Acceptance v1 |
| `GET /api/jobs/{job_id}` | Required path `job_id` | Local Job Status v1 artifact projection |
| `GET /api/validation-receipts` | Exactly one of `receipt_id`, `work_id`, or `latest=true` | Local Validation Receipt v1 |
| `GET /api/contributions` | None | Local Contribution Lookup v1 |
| `GET /api/audit-events` | Optional documented filters | Local Audit Page v1 |

## Local Job Submission v1

Required request fields are `schema_version` (integer `1`), `job_type` (non-empty string), `payload` (object), `creator_node_id` (non-empty string), `requested_validation_mode` (non-empty string), `lineage_parent_refs` (array of non-empty strings; empty is the root-lineage value), and `attribution_metadata` (object; empty is allowed). The server rejects a request missing any required field. It writes a version-1 submission manifest that preserves the creator ID, manifest reference, lineage object, and contribution attribution object.

Successful response required fields are `schema_version` (`1`), `job_id`, `status` (`accepted_pending_execution`), `manifest_ref`, `next_validation_expectation`, and `network_mode` (`local-only-no-p2p`).

Example request:

```json
{
  "schema_version": 1,
  "job_type": "echo",
  "payload": {"message": "schema example"},
  "creator_node_id": "creator-local-example",
  "requested_validation_mode": "deterministic-local",
  "lineage_parent_refs": ["data/prior-job.json"],
  "attribution_metadata": {"source": "phase-1-schema-contract"}
}
```

## Local Job Status v1

A known submission response includes `job_id`, `status`, `manifest_ref`, `creator_node_id`, `worker_node_id`, `lineage`, `contribution_attribution`, `validation`, `result`, `error`, and `network_mode`. Queued jobs have `null` worker/result/validation evidence. Completed jobs preserve a validation receipt reference and validation-gated attribution; a receipt is local evidence, not consensus.

Example completed projection (dynamic IDs and timestamps omitted):

```json
{
  "job_id": "local-job-<generated>",
  "status": "succeeded",
  "manifest_ref": "data/job-submissions/local-job-<generated>.json",
  "creator_node_id": "creator-local-example",
  "worker_node_id": "worker-local-example",
  "lineage": {"parent_refs": ["data/prior-job.json"]},
  "contribution_attribution": {
    "creator_node_id": "creator-local-example",
    "metadata": {"source": "phase-1-schema-contract"},
    "worker_node_id": "worker-local-example",
    "validated_contribution_units": 1
  },
  "validation": {"passed": true, "reason": "ok"},
  "network_mode": "local-only-no-p2p"
}
```

## Local Validation Receipt v1

`GET /api/validation-receipts` is read-only and returns persisted validation evidence. A successful receipt includes `receipt_id`, `job_id`, `creator_node_id`, `manifest_ref`, `lineage_parent_ids`, `validation_status`, `validator_identity`, `contribution_attribution`, `validation_scope`, and `evidence`. A missing receipt is rejected with 404; malformed lookup combinations are rejected with 400.

Example lookup: `GET /api/validation-receipts?work_id=local-job-<generated>`.

## Local Contribution Lookup v1

`GET /api/contributions` is read-only. Its response includes `network_mode`, `summary_status`, `accepted_work_count`, `non_accepted_work_count`, and `items`. An accepted item preserves `creator_node_id`, `contributing_node_id`, `manifest_ref`, `validation_receipt_ref`, `lineage_links`, and validation-gated attribution evidence.

Example lookup: `GET /api/contributions` after the completed job example above.

## Validation receipt

`tests/test_api_schema_contract.py` loads the submission example from this file's equivalent test fixture, exercises it through the actual FastAPI route, verifies required-field rejection for schema version, creator, lineage, and attribution, then verifies its status, validation receipt, and contribution lookup. It also confirms the documented provenance routes are present in generated `/openapi.json`.
