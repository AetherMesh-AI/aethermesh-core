# Local Node Lifecycle

AetherMesh Core uses a small local-first lifecycle model for one node runtime. The model reports what the local node is allowed to do, why it moved between states, and which persisted records must survive restarts. It does not imply public networking, production decentralization, rewards, token balances, dashboards, or later-phase coordination.

The canonical states and transition rules are implemented in `aethermesh_core.lifecycle`.

## Canonical states

| State | Purpose | Allowed next states |
| --- | --- | --- |
| `created` | A local node identity exists, but the active manifest is not ready for work. | `configured`, `failed`, `retired` |
| `configured` | The local node references an active manifest, but validation gates have not made it runnable yet. | `ready`, `failed`, `retired` |
| `ready` | Identity, active manifest, and local validation receipts permit local work to start. | `running`, `paused`, `failed`, `retired` |
| `running` | The single local node runtime is actively accepting or executing local work. | `paused`, `validating`, `failed` |
| `paused` | The runtime stopped intentionally while preserving manifest, lineage, validation, and attribution records. | `ready`, `running`, `failed`, `retired` |
| `validating` | A work result is being checked before contribution attribution can advance. | `running`, `completed`, `failed` |
| `completed` | Local work finished with validation receipts and contribution attribution linked. | `ready`, `running`, `retired` |
| `failed` | A recoverable or terminal error is visible and linked to validation evidence instead of hidden. | `configured`, `ready`, `retired` |
| `retired` | The local runtime is intentionally inactive; persisted records remain audit evidence. | none |

Invalid transitions are errors. A retired runtime has no allowed next state. A terminal failed record may only transition to `retired`; recoverable failures may return to `configured` or `ready` after the manifest, identity, validation receipt, or local runtime issue is corrected.

## Transition events and validation conditions

Each transition must be caused by an explicit local event or validation result:

- `created` → `configured`: a local config record selects an active local manifest.
- `created` → `failed`: identity or manifest discovery fails and the error is recorded.
- `created` → `retired`: the local prototype identity is intentionally retired before work starts.
- `configured` → `ready`: local manifest and identity checks pass, and required validation receipts are present or not required for this manifest.
- `configured` → `failed`: manifest, identity, lineage, receipt, or attribution checks fail.
- `configured` → `retired`: the configured local node is intentionally retired before running.
- `ready` → `running`: a local runtime marker is written for the foreground node process.
- `ready` → `paused`: the operator intentionally pauses before starting work.
- `ready` → `failed`: startup validation fails.
- `ready` → `retired`: the ready node is intentionally retired.
- `running` → `paused`: the operator stops or pauses the runtime without discarding audit links.
- `running` → `validating`: a local work result is handed to validation.
- `running` → `failed`: execution or runtime validation fails and the failure is recorded.
- `paused` → `ready`: restart recovery finds preserved records but no active runtime marker.
- `paused` → `running`: restart recovery or operator action restarts the local runtime with preserved records.
- `paused` → `failed`: restart recovery detects missing or inconsistent persisted records.
- `paused` → `retired`: the paused runtime is intentionally retired.
- `validating` → `running`: validation completes for one item and the runtime continues taking local work.
- `validating` → `completed`: validation succeeds and the work item/run is complete.
- `validating` → `failed`: validation fails; the validation error remains visible.
- `completed` → `ready`: restart recovery or operator action returns the local node to an idle ready state.
- `completed` → `running`: the local runtime immediately starts additional work with the same preserved audit links plus any new links.
- `completed` → `retired`: the completed local runtime is intentionally retired.
- `failed` → `configured`: a recoverable configuration or manifest error is corrected and must be revalidated.
- `failed` → `ready`: a recoverable runtime or receipt issue is corrected and the existing manifest is still valid.
- `failed` → `retired`: the local node is intentionally retired, or the failure is terminal.

## Persisted fields for lifecycle-changing events

Every lifecycle-changing event record must include:

- `state`: one of the canonical states above.
- `event`: the local event or validation condition that caused the transition.
- `creator_node_id`: the creator identity for the local node and any derived work.
- `active_manifest_ref`: the active local manifest reference. This is a local file or fixture reference, not a network registry.
- `lineage_refs`: local lineage records that link derived work to its origin.
- `validation_receipt_refs`: validation receipts that justify readiness, completion, failure, or attribution decisions.
- `contribution_refs`: contribution attribution records linked to validated work.
- `failure_reason`: required for `failed` records. It must preserve validation or runtime error detail instead of replacing it with a generic status.
- `failure_terminal`: boolean marker for terminal failures. When true, the only valid next state is `retired`.

Work-related transitions involving `running`, `paused`, `validating`, `completed`, or `failed` must preserve `creator_node_id`, `active_manifest_ref`, existing `lineage_refs`, existing `validation_receipt_refs`, and existing `contribution_refs`. A transition may append new receipts or attribution links, but it must not drop existing audit links after pause, failure, restart, validation, or completion paths.

## Restart recovery

Restart recovery derives state from persisted local records plus the volatile runtime marker:

1. Load the latest lifecycle event record and validate `creator_node_id` and `active_manifest_ref`.
2. Resolve the active manifest locally and keep its reference attached to the recovered state.
3. Validate referenced lineage, validation receipt, and contribution attribution records. Do not silently drop missing or malformed references.
4. If the latest persisted state is `retired`, `failed`, `completed`, `validating`, or `paused`, recover that state directly. A process marker must not hide those states.
5. If the latest persisted state is `ready` and the local runtime marker is alive, report `running`.
6. If the latest persisted state is `ready` and no runtime marker is alive, report `ready`.
7. If recovery detects missing manifests, broken receipts, or attribution mismatches, record `failed` with the concrete validation error. Treat it as recoverable unless the local operator marks it terminal.

This keeps restart behavior local and auditable: process memory can only show that a ready node is currently running; it cannot erase validation errors, terminal retirement, lineage, receipts, or contribution attribution.

## Scope boundaries

The lifecycle is scoped to a single local node runtime. It does not define peer discovery, networking, distributed consensus, reward math, tokenomics, public reputation, dashboards, or orchestration policy. Later phases can build coordination on top of these persisted local records without changing the Phase 1 requirement that creator identity, active manifest, lineage, validation receipts, and attribution remain linked across restarts.
