# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 40 files · ~22,365 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 538 nodes · 1428 edges · 15 communities (13 shown, 2 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 138 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `da955a35`
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

## God Nodes (most connected - your core abstractions)
1. `Job` - 83 edges
2. `main()` - 55 edges
3. `JobResult` - 49 edges
4. `MeshMessage` - 48 edges
5. `CliTests` - 47 edges
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

## Communities (15 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (17): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (29): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Structured result for local assignment-only dispatch., Build a local dispatch log with heartbeats and job assignments only.      This f, NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order. (+21 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (37): _node_artifact_filename(), _node_artifact_path(), Load an existing ledger and return read-only aggregate totals., Run dispatch and all available local worker inboxes as one local flow., Return a deterministic, non-merging filename for one manifest node id., run_local_flow(), summarize_ledger(), _accounted_units() (+29 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (27): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), build_message_log_document(), Build a deterministic version 1 audit document for local mesh messages., Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution. (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (21): _send_dispatch_message(), LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., MeshMessage (+13 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (26): Serialize a deterministic, intentionally small CLI summary., Serialize the record into a JSON-compatible dictionary., Serialize the message into a JSON-compatible dictionary., Serialize the result into a JSON-compatible dictionary., ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally., build_receipt_document(), _json_compatible_dict() (+18 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (26): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), build_flow_message_log_document(), build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages(), load_worker_emitted_messages() (+18 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (4): build_parser(), main(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (25): Command-line interface for the local AetherMesh prototype., Assignment-only local dispatch for manifest-backed batches., AetherMesh Core local prototype package., Contribution ledger helpers for local job results., MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Local mesh message envelopes for deterministic simulation output. (+17 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (16): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs() (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (21): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_ids_from_replayed_messages(), process_local_inbox(), Replay a saved local message log and process one node inbox., Replay a saved local message log and return payload plus structured result., InboxProcessResult, Structured result returned by one local inbox processing pass. (+13 more)

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 0`, `Community 2`, `Community 3`, `Community 7`, `Community 12`, `Community 13`, `Community 14`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 1`, `Community 5`, `Community 6`, `Community 7`, `Community 12`, `Community 13`, `Community 14`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 5` to `Community 1`, `Community 3`, `Community 6`, `Community 7`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 17 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `LocalMessageBus`) actually correct?**
  _`MeshMessage` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _125 weakly-connected nodes found - possible documentation gaps or missing edges._