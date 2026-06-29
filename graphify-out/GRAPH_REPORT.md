# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 44 files · ~25,571 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 600 nodes · 1627 edges · 20 communities (17 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 146 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `269a60a9`
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

## God Nodes (most connected - your core abstractions)
1. `Job` - 93 edges
2. `main()` - 61 edges
3. `MeshMessage` - 54 edges
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
- `LocalNodeServiceTests` --uses--> `LocalMessageBus`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/message_bus.py
- `LocalMessageBusTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_message_bus.py → src/aethermesh_core/messages.py
- `LocalNodeServiceTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/messages.py

## Import Cycles
- None detected.

## Communities (20 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (18): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+10 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (10): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order., _node_heartbeat_messages() (+2 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (30): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Contribution ledger helpers for local job results. (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (18): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., Run local jobs across local node identities using scheduler assignment.      Thi, run_local_simulation() (+10 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (47): _node_artifact_path(), Run dispatch and all available local worker inboxes as one local flow., run_local_flow(), _assert_assignment_matches_receipt(), _assert_contribution_message_matches_receipt(), _assert_equal(), _assert_result_message_matches_receipt(), audit_local_flow() (+39 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (17): AetherMesh Core local prototype package., _fallback_job_id(), _job_from_assignment_payload(), LocalNodeService, Local-only node inbox processing service for assigned work messages., Synchronous local-only handler for one node's assigned-work inbox., Process unhandled ``job_assigned`` messages addressed to this node.          The, build_text_chunk_output() (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.12
Nodes (11): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+3 more)

### Community 12 - "Community 12"
Cohesion: 0.16
Nodes (9): Deterministic local node registry for simulation roster state., _coerce_job(), NoAvailableNodesError, _normalize_capabilities(), Deterministic local scheduler for the AetherMesh prototype., Raised when local job assignment has jobs but no available nodes., Minimal scheduler view of a job., Assign jobs round-robin across available capable nodes in input order. (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (16): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs() (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (28): build_parser(), _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_artifact_filename(), _node_ids_from_replayed_messages(), process_local_inbox(), Command-line interface for the local AetherMesh prototype., Load an existing ledger and return read-only aggregate totals. (+20 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (12): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Read-only local peer roster derived from heartbeat messages. (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (43): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), build_flow_message_log_document(), build_message_log_document(), build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages() (+35 more)

### Community 17 - "Community 17"
Cohesion: 0.25
Nodes (6): _coerce_node(), LocalScheduler, Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., ScheduledNode, LocalSchedulerTests

### Community 18 - "Community 18"
Cohesion: 0.16
Nodes (10): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Assignment-only local dispatch for manifest-backed batches., Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., Build a local dispatch log with heartbeats and job assignments only.      This f, _send_dispatch_message() (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.28
Nodes (6): Register a node ID or ScheduledNode in deterministic insertion order., _RegistryNode, NodeStatus, Availability states needed by the local scheduler., Enum, str

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 0`, `Community 3`, `Community 5`, `Community 13`, `Community 14`, `Community 15`, `Community 16`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 5`, `Community 6`, `Community 13`, `Community 14`, `Community 16`, `Community 17`, `Community 18`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 16` to `Community 3`, `Community 5`, `Community 6`, `Community 7`, `Community 14`, `Community 15`, `Community 18`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `FlowAuditError`) actually correct?**
  _`MeshMessage` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _135 weakly-connected nodes found - possible documentation gaps or missing edges._