# Phase 1 API Schema Contract

Schema contract version: `1`

This is the stable, local-only contract for the provenance-bearing Phase 1 routes. It complements [the API boundary](phase-1-local-api-boundary.md); that boundary remains the route inventory and locality definition. A schema change is deliberate: additive optional fields are compatible within version 1; removing, renaming, changing a field type, or making an optional field required requires a new schema version, updated examples, and a migration note.

## `POST /api/jobs` — local work submission

Request schema version: `1`. Required fields are `job_type`, `payload`, `creator_node_id`, `requested_validation_mode`, `lineage_parent_refs`, and `attribution_metadata`. Empty lineage is allowed only for root work; empty attribution metadata is allowed, but the persisted attribution always binds `creator_node_id`.

```json
{
  "job_type": "echo",
  "payload": {"message": "hello"},
  "creator_node_id": "creator-local-a",
  "requested_validation_mode": "deterministic-local",
  "lineage_parent_refs": [],
  "attribution_metadata": {"source": "local-example"}
}
```

A successful response has `job_id`, `status`, `manifest_ref`, `next_validation_expectation`, and `network_mode`. Its immutable manifest has `version: 1`, `manifest_type: "local_job_submission"`, the creator ID, lineage object, and contribution-attribution object.

## `GET /api/validation-receipts` — validation result lookup

Query schema version: `1`. Supply exactly one selector: non-empty `receipt_id`, a `work_id` in `local-job-<32 lowercase hex>` form, or `latest=true`.

```json
{"work_id": "local-job-0123456789abcdef0123456789abcdef"}
```

The response schema version is `1`. Required provenance fields are `receipt_id`, `work_id`, `creator_node_id`, `manifest_ref`, `validation_status`, `validation`, `validator_identity`, `lineage_parent_ids`, `contribution_attribution`, and `evidence.receipt_ref`/`result_ref`/`status_ref`. A missing receipt is a `404`; malformed or ambiguous selectors are `400`.

```json
{
  "schema_version": 1,
  "network_mode": "local-only-no-p2p",
  "validation_scope": "local-only-not-consensus",
  "receipt_id": "local-validation-receipt-local-job-0123456789abcdef0123456789abcdef",
  "work_id": "local-job-0123456789abcdef0123456789abcdef",
  "creator_node_id": "creator-local-a",
  "manifest_ref": "data/job-submissions/local-job-0123456789abcdef0123456789abcdef.json",
  "validation_status": "passed",
  "validation": {"valid": true, "reason": "ok"},
  "validation_timestamp": 1,
  "validation_timestamp_source": "receipt_record",
  "validator_identity": "worker-local-a",
  "lineage_parent_ids": [],
  "contribution_attribution": {"creator_node_id": "creator-local-a", "metadata": {}},
  "evidence": {
    "receipt_ref": "data/job-validation-receipts/local-job-0123456789abcdef0123456789abcdef.json",
    "result_ref": "data/job-results/local-job-0123456789abcdef0123456789abcdef.json",
    "status_ref": "data/job-status/local-job-0123456789abcdef0123456789abcdef.json"
  }
}
```

## `GET /api/contributions` — contribution lookup

Request schema version: `1`: this route takes no parameters. The response is local-only and has `network_mode`, `summary_status`, `accepted_work_count`, `non_accepted_work_count`, and `items`. Each accepted item records `creator_node_id`, `manifest_ref`, `validation_receipt_ref`, and `lineage_links`; it is not a balance or reward claim.

```json
{
  "network_mode": "local-only-no-p2p",
  "summary_status": "empty",
  "accepted_work_count": 0,
  "non_accepted_work_count": 0,
  "items": []
}
```

## Local node registration/startup

There is no node-registration HTTP endpoint. The local startup boundary creates or loads identity and returns `LocalStartupResult`. Its version-1 startup manifest and validation receipt require `node_id`, `creator_node_id`, manifest reference/hash, validation evidence, and startup lineage. See [the API boundary](phase-1-local-api-boundary.md#node-createload-contract) for the response example and [local node identity](local-node-identity.md) for the persisted identity schema.

## Migration note: schema contract version 1

Before this contract, `lineage_parent_refs` and `attribution_metadata` on `POST /api/jobs` were defaulted when omitted. They are required as of schema contract version 1 so accepted work explicitly declares lineage and attribution intent. Local callers must send `[]` for root work and `{}` when no extra attribution metadata exists. No stored artifact format changed.
