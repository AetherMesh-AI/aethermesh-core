# Phase 1 API Schema Contract

Schema contract version: `1`. This is the stable, local-only companion to [the API boundary](phase-1-local-api-boundary.md). The boundary document indexes every localhost route and its behavior; this document fixes the versioned provenance payloads that can be persisted or exchanged between local process runs.

Compatibility rule: additive optional fields are allowed within schema version 1. Removing, renaming, or changing the meaning or type of a required field requires a new schema version, an updated example, and a migration note in this document.

Migration note: before this baseline, `POST /api/jobs` accepted an unversioned request and defaulted omitted `lineage_parent_refs` and `attribution_metadata` to empty values. Version 1 deliberately replaces that prototype-only shape: callers must send `schema_version: 1` and must send both provenance fields explicitly. The server rejects the former unversioned shape rather than guessing a contract version. Responses from submission, job status, validation-receipt lookup, and contribution lookup now identify schema version 1.

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

A known submission response includes `schema_version` (`1`), `job_id`, `status`, `manifest_ref`, `creator_node_id`, `worker_node_id`, `lineage`, `contribution_attribution`, `validation`, `result`, `error`, and `network_mode`. Queued jobs have `null` worker/result/validation evidence. Completed jobs preserve a validation receipt reference and validation-gated attribution; a receipt is local evidence, not consensus. A not-found response contains `schema_version`, `job_id`, `status: not_found`, and `error`.

Example completed projection (dynamic IDs and timestamps omitted):

```json
{
  "schema_version": 1,
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
  "validation": {
    "passed": true,
    "reason": "ok",
    "receipt_ref": "data/job-validation-receipts/local-job-<generated>.json"
  },
  "result": {
    "ref": "data/job-results/local-job-<generated>.json",
    "summary": "schema example"
  },
  "error": null,
  "network_mode": "local-only-no-p2p"
}
```

## Local Validation Receipt v1

`GET /api/validation-receipts` is read-only and returns persisted validation evidence. A successful receipt includes `schema_version` (`1`), `receipt_id`, `work_id`, `creator_node_id`, `manifest_ref`, `lineage_parent_ids`, `validation_status`, `validator_identity`, `contribution_attribution`, `validation_scope`, `validation` (including `job_id`), and `evidence`. A missing receipt is rejected with 404; malformed lookup combinations are rejected with 400.

Example lookup: `GET /api/validation-receipts?work_id=local-job-<generated>`.

Example response (dynamic timestamp omitted):

```json
{
  "schema_version": 1,
  "receipt_id": "local-validation-receipt-local-job-<generated>",
  "work_id": "local-job-<generated>",
  "creator_node_id": "creator-local-example",
  "manifest_ref": "data/job-submissions/local-job-<generated>.json",
  "lineage_parent_ids": ["data/prior-job.json"],
  "validation_status": "passed",
  "validator_identity": "worker-local-example",
  "contribution_attribution": {"validated_contribution_units": 1},
  "validation_scope": "local-only-not-consensus",
  "validation": {"job_id": "local-job-<generated>", "valid": true},
  "evidence": {"result_ref": "data/job-results/local-job-<generated>.json"}
}
```

## Local Contribution Lookup v1

`GET /api/contributions` is read-only. Its response includes `schema_version` (`1`), `network_mode`, `summary_status`, `accepted_work_count`, `non_accepted_work_count`, and `items`. An accepted item preserves `creator_node_id`, `contributing_node_id`, `manifest_ref`, `validation_receipt_ref`, `lineage_links`, and validation-gated acceptance evidence.

Example lookup: `GET /api/contributions` after the completed job example above.

```json
{
  "schema_version": 1,
  "network_mode": "local-only-no-p2p",
  "summary_status": "recorded",
  "accepted_work_count": 1,
  "non_accepted_work_count": 0,
  "items": [{
    "work_item_id": "local-job-<generated>",
    "status": "succeeded",
    "acceptance_status": "accepted",
    "creator_node_id": "creator-local-example",
    "contributing_node_id": "worker-local-example",
    "manifest_ref": "data/job-submissions/local-job-<generated>.json",
    "status_ref": "data/job-status/local-job-<generated>.json",
    "validation_receipt_ref": "data/job-validation-receipts/local-job-<generated>.json",
    "lineage_links": ["data/prior-job.json"],
    "timestamps": {"submitted_at": 0},
    "evidence_errors": []
  }]
}
```

## Validation receipt

`tests/test_api_schema_contract.py` loads every JSON example in this document, checks each example against the documented required-field contract, exercises the submission through the actual FastAPI route, verifies required-field rejection for schema version, creator, lineage, and attribution, then verifies its status, validation receipt, and contribution lookup. It also confirms the documented provenance routes and methods are present in generated `/openapi.json`.
