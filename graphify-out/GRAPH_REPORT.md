# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 47 files · ~28,082 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 643 nodes · 1762 edges · 18 communities (16 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 150 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2ad85971`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 19|Community 19]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 102 edges
2. `main()` - 65 edges
3. `MeshMessage` - 61 edges
4. `JobResult` - 57 edges
5. `CliTests` - 51 edges
6. `ScheduledNode` - 43 edges
7. `NodeIdentity` - 38 edges
8. `validate_job_result()` - 38 edges
9. `ContributionLedger` - 36 edges
10. `LocalRunner` - 35 edges

## Surprising Connections (you probably didn't know these)
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `ReceiptTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_receipts.py → src/aethermesh_core/ledger.py
- `LocalNodeServiceTests` --uses--> `LocalMessageBus`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/message_bus.py
- `LocalTransportTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_local_transport.py → src/aethermesh_core/messages.py
- `MessageLogTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_message_log.py → src/aethermesh_core/messages.py

## Import Cycles
- None detected.

## Communities (18 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (25): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+17 more)

### Community 1 - "Community 1"
Cohesion: 0.41
Nodes (3): _assignment(), LocalNodeServiceTests, _service()

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (30): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Record one result and return its local contribution record.          Only comple (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.10
Nodes (20): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), build_message_log_document(), Build a deterministic version 1 audit document for local mesh messages., Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution. (+12 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (48): _node_artifact_path(), Run dispatch and all available local worker inboxes as one local flow., run_local_flow(), _assert_assignment_matches_receipt(), _assert_contribution_message_matches_receipt(), _assert_equal(), _assert_result_message_matches_receipt(), audit_local_flow() (+40 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (23): Command-line interface for the local AetherMesh prototype., Assignment-only local dispatch for manifest-backed batches., AetherMesh Core local prototype package., Contribution ledger helpers for local job results., MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., JSON-backed local message log persistence for batch simulations. (+15 more)

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (32): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_artifact_filename(), _node_ids_from_replayed_messages(), process_local_inbox(), Return a deterministic, non-merging filename for one manifest node id., Replay a saved local message log or local transport inbox for one node., Replay saved local messages and return payload plus structured result. (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (7): build_parser(), main(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ArgumentParser, CliTests, LocalTransportCliTests

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (20): _atomic_write_json(), _load_inbox_document(), load_local_inbox(), local_inbox_path(), LocalTransportError, materialize_local_inboxes(), _message_from_inbox_entry(), File-backed local transport inboxes for addressed mesh messages.  Version 1 loca (+12 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (13): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs(), _parse_node_entry() (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (13): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace., Raised when a local node-state JSON file cannot be safely loaded or saved., Durable local record of assignment messages already processed by one node. (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (12): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Read-only local peer roster derived from heartbeat messages. (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (27): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), _load_message_log_document(), load_message_log_messages(), load_worker_emitted_messages(), _message_from_document_entry(), MessageLogPersistenceError (+19 more)

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (33): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., Build a local dispatch log with heartbeats and job assignments only.      This f, LocalJobBatch, Validated local batch inputs for the local simulation path. (+25 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 0`, `Community 3`, `Community 5`, `Community 6`, `Community 7`, `Community 12`, `Community 13`, `Community 15`, `Community 16`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 5`, `Community 6`, `Community 7`, `Community 13`, `Community 16`, `Community 19`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 7` to `Community 0`, `Community 1`, `Community 3`, `Community 5`, `Community 6`, `Community 12`, `Community 15`, `Community 16`, `Community 19`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `FlowAuditError`) actually correct?**
  _`MeshMessage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _142 weakly-connected nodes found - possible documentation gaps or missing edges._