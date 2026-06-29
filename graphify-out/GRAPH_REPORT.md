# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 44 files · ~24,263 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 573 nodes · 1521 edges · 20 communities (18 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 144 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b8f04670`
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
1. `Job` - 83 edges
2. `main()` - 61 edges
3. `MeshMessage` - 51 edges
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
- `MessageLogTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_message_log.py → src/aethermesh_core/messages.py
- `ReceiptTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_receipts.py → src/aethermesh_core/messages.py
- `LocalNodeServiceTests` --uses--> `NodeIdentity`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/models.py

## Import Cycles
- None detected.

## Communities (20 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (17): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (8): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order., NodeRegistryTests

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (26): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, Record one result and return its local contribution record.          Only comple, Return deterministic aggregate totals for one local node., Return node ids present in the ledger in deterministic order. (+18 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (23): Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally., build_receipt_document(), Build a deterministic version 1 receipt document.      Receipts are derived from (+15 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.20
Nodes (9): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Structured result for local assignment-only dispatch., Build a local dispatch log with heartbeats and job assignments only.      This f, _send_dispatch_message() (+1 more)

### Community 6 - "Community 6"
Cohesion: 0.26
Nodes (6): _coerce_node(), LocalScheduler, Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., ScheduledNode, LocalSchedulerTests

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (26): LocalMessageBus, MessageDelivery, A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node. (+18 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (6): build_parser(), main(), Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (24): Command-line interface for the local AetherMesh prototype., Assignment-only local dispatch for manifest-backed batches., Read-only audit checks for completed local flow artifact directories., AetherMesh Core local prototype package., Contribution ledger helpers for local job results., Synchronous in-memory message bus for local AetherMesh simulation., JSON-backed local message log persistence for batch simulations., Local mesh message envelopes for deterministic simulation output. (+16 more)

### Community 13 - "Community 13"
Cohesion: 0.08
Nodes (23): Run a local simulation from a validated JSON manifest., run_local_batch(), Serialize a deterministic, intentionally small CLI summary., load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry() (+15 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (21): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_ids_from_replayed_messages(), process_local_inbox(), Replay a saved local message log and process one node inbox., Replay a saved local message log and return payload plus structured result., InboxProcessResult, Structured result returned by one local inbox processing pass. (+13 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (12): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Read-only local peer roster derived from heartbeat messages. (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.06
Nodes (45): _node_artifact_filename(), _node_artifact_path(), Load an existing ledger and return read-only aggregate totals., Run dispatch and all available local worker inboxes as one local flow., Return a deterministic, non-merging filename for one manifest node id., run_local_flow(), summarize_ledger(), audit_local_flow() (+37 more)

### Community 17 - "Community 17"
Cohesion: 0.19
Nodes (6): _node_heartbeat_messages(), Return deterministic local heartbeat payloads for available nodes only., Run local jobs across local node identities using scheduler assignment.      Thi, run_local_simulation(), _validation_summary(), LocalSimulationTests

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (11): build_dispatch_message_log_document(), Build a deterministic version 1 assignment-only dispatch document., JobAssignment, NoAvailableNodesError, Raised when local job assignment has jobs but no available nodes., Structured local assignment of one job to one node., Serialize the assignment into a JSON-compatible dictionary., Assign jobs round-robin across available capable nodes in input order. (+3 more)

### Community 19 - "Community 19"
Cohesion: 0.28
Nodes (6): Register a node ID or ScheduledNode in deterministic insertion order., _RegistryNode, NodeStatus, Availability states needed by the local scheduler., Enum, str

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 0`, `Community 5`, `Community 12`, `Community 13`, `Community 14`, `Community 15`, `Community 16`?**
  _High betweenness centrality (0.157) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 12`, `Community 13`, `Community 14`, `Community 16`, `Community 17`, `Community 18`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 7` to `Community 3`, `Community 5`, `Community 12`, `Community 14`, `Community 15`, `Community 16`, `Community 18`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `LocalMessageBus`) actually correct?**
  _`MeshMessage` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _133 weakly-connected nodes found - possible documentation gaps or missing edges._