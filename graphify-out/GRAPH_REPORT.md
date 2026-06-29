# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 44 files · ~24,740 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 586 nodes · 1579 edges · 16 communities (14 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 146 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fd447741`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 83 edges
2. `main()` - 61 edges
3. `MeshMessage` - 54 edges
4. `CliTests` - 51 edges
5. `JobResult` - 49 edges
6. `ScheduledNode` - 41 edges
7. `ContributionLedger` - 36 edges
8. `run_local_simulation()` - 33 edges
9. `LocalMessageBus` - 30 edges
10. `NodeIdentity` - 30 edges

## Surprising Connections (you probably didn't know these)
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `ReceiptTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_receipts.py → src/aethermesh_core/ledger.py
- `LocalMessageBusTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_message_bus.py → src/aethermesh_core/messages.py
- `LocalNodeServiceTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/messages.py
- `ReceiptTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_receipts.py → src/aethermesh_core/messages.py

## Import Cycles
- None detected.

## Communities (16 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (20): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+12 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (34): dispatch_local_batch(), LocalDispatchResult, Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., Build a local dispatch log with heartbeats and job assignments only.      This f, LocalJobBatch, Validated local batch inputs for the local simulation path., Return manifest node IDs in deterministic manifest order. (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (30): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Record one result and return its local contribution record.          Only comple (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.10
Nodes (25): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., LocalNodeService, ProcessedAssignment (+17 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (42): _node_artifact_path(), Run dispatch and all available local worker inboxes as one local flow., run_local_flow(), _assert_assignment_matches_receipt(), _assert_contribution_message_matches_receipt(), _assert_equal(), _assert_result_message_matches_receipt(), audit_local_flow() (+34 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (11): LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., LocalMessageBusTests, _message() (+3 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (6): build_parser(), main(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (30): _node_artifact_filename(), Command-line interface for the local AetherMesh prototype., Return a deterministic, non-merging filename for one manifest node id., _node_heartbeat_payloads(), Assignment-only local dispatch for manifest-backed batches., _send_dispatch_message(), AetherMesh Core local prototype package., Contribution ledger helpers for local job results. (+22 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (13): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs(), _parse_node_entry() (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (21): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_ids_from_replayed_messages(), process_local_inbox(), Replay a saved local message log and process one node inbox., Replay a saved local message log and return payload plus structured result., InboxProcessResult, Structured result returned by one local inbox processing pass. (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (12): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Read-only local peer roster derived from heartbeat messages. (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (35): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), build_flow_message_log_document(), build_message_log_document(), build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages() (+27 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 0`, `Community 3`, `Community 5`, `Community 12`, `Community 13`, `Community 14`, `Community 15`, `Community 16`?**
  _High betweenness centrality (0.155) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 1`, `Community 12`, `Community 13`, `Community 14`, `Community 16`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 16` to `Community 1`, `Community 3`, `Community 5`, `Community 7`, `Community 12`, `Community 14`, `Community 15`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `FlowAuditError`) actually correct?**
  _`MeshMessage` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _133 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.10256410256410256 - nodes in this community are weakly interconnected._