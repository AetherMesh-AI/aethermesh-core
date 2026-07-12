# Phase 1 API Schema Contract

Schema contract version: `1`. This is the stable, local-only companion to [the API boundary](phase-1-local-api-boundary.md). The boundary document indexes every localhost route and its behavior; this document fixes the versioned provenance payloads that can be persisted or exchanged between local process runs.

Compatibility rule: additive optional fields are allowed within schema version 1. Removing, renaming, or changing the meaning or type of a required field requires a new schema version, an updated example, and a migration note in this document.

Migration note: before this baseline, `POST /api/jobs` accepted an unversioned request and defaulted omitted `lineage_parent_refs` and `attribution_metadata` to empty values. Version 1 deliberately replaces that prototype-only shape: callers must send `schema_version: 1` and must send both provenance fields explicitly. The server rejects the former unversioned shape rather than guessing a contract version. Responses from submission, job status, validation-receipt lookup, and contribution lookup now identify schema version 1.

## Local API error envelope

Every HTTP failure from the local API uses this stable envelope. Successful response shapes are unchanged.

```jsonc
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "The request is invalid.",
    "details": {}
  },
  "request_id": "local request trace identifier"
}
```

`request_id` is a fresh local trace identifier for correlating a caller response with local process logs. `error.details` is deliberately an empty object in version 1: API failures must not return exception text, stack traces, creator node IDs, manifests, receipts, lineage records, or contribution-attribution data. Local logs retain the original diagnostic.

The current stable codes are `INVALID_INPUT` (400 or 405), `NOT_FOUND` (404 route lookup), `MISSING_MANIFEST` (404), `VALIDATION_FAILURE` (400 or 404 when evidence is absent), `LINEAGE_LOOKUP_FAILURE` (400), `CONTRIBUTION_ATTRIBUTION_FAILURE` (400), and `INTERNAL_ERROR` (500). Callers should test `error.code` rather than response messages or log text.

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

Required request fields are `schema_version` (integer `1`), `job_type` (non-empty string), `requested_capability` (object containing exactly one canonical local work `identifier`, such as `work.echo`), `input_payload` (object with `payload_type`, object `content`, and optional object `parameters`), `creator_node_id` (a safe non-empty local identifier), `requested_validation_mode` (non-empty string), `lineage_parent_refs` (array of safe relative local references; empty is the root-lineage value), and `attribution_metadata` (object; empty is allowed). `requested_capability` must contain exactly one canonical local work `identifier` matching `job_type` (for example, `work.echo` for `echo`). The requested capability is resolved only against this receiving node's local capability manifest; unknown, disabled, or malformed identifiers are rejected before a submission manifest, status record, lineage, contribution attribution, or validation receipt is created. The payload is canonically serialized as UTF-8 JSON, limited to 65,536 bytes, and recorded with a `sha256:<64 lowercase hex>` input-payload hash in the manifest. The server rejects a request missing any required field. Creator IDs and lineage references reject path traversal, absolute paths, URI-shaped values, and private-key-shaped references. It writes a version-1 submission manifest that preserves the creator ID, requested capability, manifest reference, lineage object, and contribution attribution object.

`requester_identity` is optional request-origin evidence, separate from creator, worker, validator, lineage, and contribution identities. Omit it or set it to `null` when absent; use exactly one of `{"requesting_node_id": "..."}`, `{"local_requester_identity": "..."}`, or `{"status": "unknown"}` when known or explicitly unknown. The local prototype stores this value in the submission manifest and validation receipt without treating it as remote-network evidence.

`local_safety` is optional and local-only. When absent, jobs run through the normal deterministic runner without a timeout or cancellation control. When needed for operator safety, it may contain `timeout_seconds` (0 through 60) and/or `cancellation_requested` (boolean). A declared timeout runs in an isolated local process and stops it on expiry; a requested cancellation stops before execution. Both outcomes are persisted as failed local validation evidence with zero validated contribution units, while retaining the original manifest, creator, lineage, and attribution fields. This is not distributed scheduling or a remote cancellation protocol.

Version 1 intentionally accepts unknown additive submission fields for forward compatibility, but does not persist them in the local submission manifest. Unknown query parameters are likewise ignored by the local read-only routes. Known path and audit artifact IDs remain strict: job/manifest IDs, receipt IDs, lineage IDs, and contribution-attribution IDs must use their documented local ID forms.

Successful response required fields are `schema_version` (`1`), `job_id`, `status` (`queued`), `manifest_ref`, `next_validation_expectation`, and `network_mode` (`local-only-no-p2p`).

Example request:

```json
{
  "schema_version": 1,
  "job_type": "echo",
  "requested_capability": {"identifier": "work.echo"},
  "input_payload": {"payload_type": "json", "content": {"message": "schema example"}},
  "creator_node_id": "creator-local-example",
  "requester_identity": {"local_requester_identity": "developer-cli"},
  "requested_validation_mode": "deterministic-local",
  "lineage_parent_refs": ["data/prior-job.json"],
  "attribution_metadata": {"source": "phase-1-schema-contract"}
}
```

## Local Job Status v1

A known submission response includes `schema_version` (`1`), `job_id`, `status`, `manifest_ref`, `creator_node_id`, `requested_capability`, `requester_identity`, `worker_node_id`, `lineage`, `contribution_attribution`, `timestamps`, `state_audit_refs`, `validation`, `result`, `error`, and `network_mode`. Every persisted status record retains its creator ID, requested capability, manifest reference, lineage, contribution attribution, timestamps, and append-only local state-audit reference.

The only local job states are: `created` (a submission manifest and initial local record exist), `queued` (the created record is ready for one local execution attempt), `running` (a worker is executing the queued job), `succeeded` (execution and local validation completed successfully), `failed` (execution or local validation completed unsuccessfully), and `canceled` (the job was stopped locally before a terminal result). Valid transitions are only `created -> queued`, `queued -> running`, `running -> succeeded`, `running -> failed`, and `created`, `queued`, or `running -> canceled`. Terminal `succeeded`, `failed`, and `canceled` jobs cannot be executed or restarted in place; a replacement must be a new job with explicit lineage back to the prior job. Each transition appends a local audit entry before the current status record is updated; manifests and inherited attribution are never overwritten by a transition.

Queued jobs have `null` worker/result/validation evidence. Completed jobs preserve a validation receipt reference and validation-gated attribution; a receipt is local evidence, not consensus. A well-formed but unknown local job ID returns `schema_version`, `job_id`, `status: not_found`, and `error`; malformed path IDs are rejected as invalid input.

Example completed projection (dynamic IDs and timestamps omitted):

```json
{
  "schema_version": 1,
  "job_id": "local-job-<generated>",
  "status": "succeeded",
  "manifest_ref": "data/job-submissions/local-job-<generated>.json",
  "creator_node_id": "creator-local-example",
  "requested_capability": {"identifier": "work.echo"},
  "requester_identity": {"local_requester_identity": "developer-cli"},
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

`GET /api/validation-receipts` is read-only and returns persisted validation evidence. A successful receipt includes `schema_version` (`1`), `receipt_id`, `work_id`, `creator_node_id`, `requester_identity`, `manifest_ref`, `input_payload_hash`, `lineage_parent_ids`, `validation_status`, `validator_identity`, `contribution_attribution`, `validation_scope`, `validation` (including `job_id`), and `evidence`. The payload hash must match the referenced manifest's canonical input payload. A missing receipt is rejected with 404; malformed lookup combinations are rejected with 400.

Example lookup: `GET /api/validation-receipts?work_id=local-job-<generated>`.

Example response (dynamic timestamp omitted):

```json
{
  "schema_version": 1,
  "receipt_id": "local-validation-receipt-local-job-<generated>",
  "work_id": "local-job-<generated>",
  "creator_node_id": "creator-local-example",
  "requester_identity": {"local_requester_identity": "developer-cli"},
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
