# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 47 files · ~27,286 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 631 nodes · 1718 edges · 22 communities (20 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 149 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a169ea77`
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
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 93 edges
2. `main()` - 65 edges
3. `MeshMessage` - 61 edges
4. `JobResult` - 53 edges
5. `CliTests` - 51 edges
6. `ScheduledNode` - 42 edges
7. `ContributionLedger` - 36 edges
8. `NodeIdentity` - 35 edges
9. `run_local_simulation()` - 33 edges
10. `validate_job_result()` - 33 edges

## Surprising Connections (you probably didn't know these)
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `ReceiptTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_receipts.py → src/aethermesh_core/ledger.py
- `LocalTransportTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_local_transport.py → src/aethermesh_core/messages.py
- `MessageLogTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_message_log.py → src/aethermesh_core/messages.py
- `ReceiptTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_receipts.py → src/aethermesh_core/messages.py

## Import Cycles
- None detected.

## Communities (22 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (17): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.20
Nodes (6): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Return JSON-compatible roster entries in registration order., _node_heartbeat_messages(), Return deterministic local heartbeat payloads for available nodes only., NodeRegistryTests

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (30): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Record one result and return its local contribution record.          Only comple (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (27): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally. (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (69): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., Run dispatch and all available local worker inboxes as one local flow., run_local_flow(), _assert_assignment_matches_receipt(), _assert_contribution_message_matches_receipt(), _assert_equal(), _assert_result_message_matches_receipt() (+61 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (31): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_artifact_filename(), _node_artifact_path(), _node_ids_from_replayed_messages(), process_local_inbox(), Command-line interface for the local AetherMesh prototype., Return a deterministic, non-merging filename for one manifest node id. (+23 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (22): _send_dispatch_message(), LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., MeshMessage (+14 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (7): build_parser(), main(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ArgumentParser, CliTests, LocalTransportCliTests

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (20): _atomic_write_json(), _load_inbox_document(), load_local_inbox(), local_inbox_path(), LocalTransportError, materialize_local_inboxes(), _message_from_inbox_entry(), File-backed local transport inboxes for addressed mesh messages.  Version 1 loca (+12 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (16): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs() (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (13): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace., Raised when a local node-state JSON file cannot be safely loaded or saved., Durable local record of assignment messages already processed by one node. (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (12): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Read-only local peer roster derived from heartbeat messages. (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.20
Nodes (7): JobAssignment, NoAvailableNodesError, Raised when local job assignment has jobs but no available nodes., Structured local assignment of one job to one node., Serialize the assignment into a JSON-compatible dictionary., Assign jobs round-robin across available capable nodes in input order., _node_roster_entry()

### Community 17 - "Community 17"
Cohesion: 0.26
Nodes (3): LocalScheduler, In-memory deterministic scheduler for local prototype jobs., LocalSchedulerTests

### Community 18 - "Community 18"
Cohesion: 0.20
Nodes (9): dispatch_local_batch(), _node_heartbeat_payloads(), Build a local dispatch log with heartbeats and job assignments only.      This f, Return scheduler-compatible nodes in registration order., _coerce_node(), _normalize_capabilities(), Local scheduler view of a node., ScheduledNode (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (9): Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., _RegistryNode, NodeStatus, Availability states needed by the local scheduler., Enum (+1 more)

### Community 20 - "Community 20"
Cohesion: 0.50
Nodes (3): LocalDispatchResult, Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary.

### Community 21 - "Community 21"
Cohesion: 0.50
Nodes (3): LocalSimulationResult, Structured, deterministic output from a local multi-node simulation., Serialize the simulation result into a JSON-compatible dictionary.          Vali

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 0`, `Community 3`, `Community 5`, `Community 6`, `Community 12`, `Community 13`, `Community 15`?**
  _High betweenness centrality (0.155) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 5`, `Community 6`, `Community 7`, `Community 13`, `Community 16`, `Community 17`, `Community 18`, `Community 20`, `Community 21`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 7` to `Community 3`, `Community 5`, `Community 6`, `Community 12`, `Community 15`, `Community 16`, `Community 20`, `Community 21`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `FlowAuditError`) actually correct?**
  _`MeshMessage` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _141 weakly-connected nodes found - possible documentation gaps or missing edges._