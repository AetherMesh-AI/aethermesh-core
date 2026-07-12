# Local API Schema Contract v1

This is the stable, local-first Phase 1 API contract. It governs localhost routes and the four provenance-bearing local operations. It does not promise peer networking, consensus, or a remote control plane.

Compatibility policy: additive optional fields are compatible within v1. A removed field, changed field type, changed requiredness, or changed meaning requires a new schema version, updated examples, and a migration note in the table below. There are no breaking changes recorded for v1.

## Route inventory

| Route | Method | Request schema | Response schema |
| --- | --- | --- | --- |
| `/health` | GET | none | `HealthResponse` |
| `/status`, `/api/status`, `/node`, `/api/node` | GET | none | `NodeStatusResponse` |
| `/version`, `/api/package` | GET | none | `PackageResponse` |
| `/peers`, `/api/peers` | GET | none | `PeerListResponse` |
| `/api/jobs` | GET | none | `JobListResponse` |
| `/api/jobs` | POST | `LocalWorkSubmissionRequestV1` | `LocalWorkSubmissionAcceptedV1` |
| `/api/jobs/{job_id}` | GET | path `job_id` | `LocalWorkStatusResponse` or `LocalWorkNotFoundResponse` |
| `/api/contributions` | GET | none | `ContributionLookupResponse` |
| `/api/validation-receipts` | GET | exactly one of query `receipt_id`, `work_id`, or `latest=true` | `ValidationReceiptResponseV1` |
| `/api/audit-events` | GET | documented query filters | `AuditEventsResponseV1` |
| `/capabilities`, `/api/capabilities` | GET | none | `CapabilitiesResponseV1` |
| `/api/model-manifests` | GET | none | `ModelManifestInspectionResponseV1` |
| `/api/network` | GET | none | `NetworkHealthResponse` |
| `/logs`, `/api/logs`, `/api/events` | GET | none | `LogEventsResponse` |
| `/shutdown`, `/restart` | POST | none | `LocalSignalResponse` |

`/` is the HTML dashboard. FastAPI publishes the same route inventory at `/openapi.json`; the contract verification checks that every JSON route above is published there.

## Provenance-bearing schemas

### LocalWorkSubmissionRequestV1

Required: `schema_version` (integer, exactly `1`), `job_type` (non-empty string), `payload` (object), `creator_node_id` (non-empty string), `requested_validation_mode` (non-empty string), `lineage_parent_refs` (array of non-empty strings; an empty array means no known parent), and `attribution_metadata` (object; an empty object means no additional metadata).

The submission manifest persisted by the route has `version: 1`, a generated job ID, the creator node ID, the lineage object, and contribution attribution containing the same creator node ID. Versionless requests remain supported only as the legacy local compatibility path; new callers must send v1.

### LocalWorkSubmissionAcceptedV1

Required: `schema_version` (integer `1`), `job_id`, `status` (`accepted_pending_execution`), `manifest_ref`, `next_validation_expectation` (`pending_requested_local_validation`), and `network_mode` (`local-only-no-p2p`). Acceptance records a manifest only; it is not execution, validation, or credit.

### LocalWorkStatusResponse

For an existing job: `job_id`, `status`, `manifest_ref`, `creator_node_id`, `worker_node_id`, `lineage`, `contribution_attribution`, `validation`, `result`, `error`, and `network_mode`. The creator and manifest references are always retained. A completed status retains validation receipt evidence and validation-gated attribution. For unknown jobs, the stable `LocalWorkNotFoundResponse` has `job_id`, `status: not_found`, and `error: local job not found`.

### ValidationReceiptResponseV1

Required: `schema_version` (integer `1`), `network_mode`, `validation_scope`, `receipt_id`, `work_id`, `creator_node_id`, `manifest_ref`, `validation_status`, `validation`, `validation_timestamp`, `validator_identity`, `lineage_parent_ids`, `contribution_attribution`, and `evidence`. `evidence` requires receipt, result, and status references. This response reads recorded local validation only; no API route records a receipt directly.

### ContributionLookupResponse

Required: `network_mode`, `summary_status`, `accepted_work_count`, `non_accepted_work_count`, and `items`. Each accepted item preserves its `creator_node_id`, `contributing_node_id`, `manifest_ref`, `validation_receipt_ref`, and `lineage_links`. It reports local validation evidence, not rewards or consensus.

### AuditEventsResponseV1

Required: `schema_version` (integer `1`), `network_mode`, `query`, `total_matching`, and `events`. Each event carries actor and creator node IDs, validation status, and artifacts containing the manifest reference, lineage parent references, contribution attribution, and receipt reference when execution occurred.

## Examples and validation

The machine-validated examples live beside this contract under `examples/api-contract-v1/`:

- `local-node-registration-response.json` — local startup/create-load response (there is no remote registration route).
- `work-submission-request.json` — v1 local work submission.
- `validation-receipt-response.json` — recorded local validation evidence.
- `contribution-lookup-response.json` — contribution lookup.

Run `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_api_contract.py --receipt docs/validation-receipts/phase-1-step-36-schema-validation.json` to validate every example and verify the published FastAPI routes. The receipt is local test evidence for this contract.

## Migration notes

| Version | Change | Migration |
| --- | --- | --- |
| v1 | Initial documented local API contract. | New submission callers send `schema_version: 1` and explicitly include empty `lineage_parent_refs` and `attribution_metadata` when no values are known. |
