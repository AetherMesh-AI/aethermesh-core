# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 38 files · ~18,655 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 482 nodes · 1226 edges · 16 communities (12 shown, 4 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 131 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ed34fc0c`
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

## God Nodes (most connected - your core abstractions)
1. `Job` - 67 edges
2. `main()` - 49 edges
3. `CliTests` - 42 edges
4. `MeshMessage` - 40 edges
5. `ScheduledNode` - 40 edges
6. `JobResult` - 38 edges
7. `ContributionLedger` - 34 edges
8. `run_local_simulation()` - 33 edges
9. `LocalMessageBus` - 30 edges
10. `NodeRegistry` - 28 edges

## Surprising Connections (you probably didn't know these)
- `JobManifestTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_job_manifest.py → src/aethermesh_core/job_manifest.py
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `LocalNodeServiceTests` --uses--> `LocalMessageBus`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/message_bus.py
- `LocalMessageBusTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_message_bus.py → src/aethermesh_core/messages.py
- `LocalNodeServiceTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/messages.py

## Import Cycles
- None detected.

## Communities (16 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.10
Nodes (22): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+14 more)

### Community 1 - "Community 1"
Cohesion: 0.05
Nodes (37): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Assignment-only local dispatch for manifest-backed batches., Structured result for local assignment-only dispatch., Build a local dispatch log with heartbeats and job assignments only.      This f, _send_dispatch_message(), NodeRegistry (+29 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (30): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Contribution ledger helpers for local job results. (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (19): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., build_text_stats_output(), Run one local job and return a structured result. (+11 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (11): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (22): Run a local simulation from a validated JSON manifest., run_local_batch(), Serialize a deterministic, intentionally small CLI summary., load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry() (+14 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (33): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), build_message_log_document(), build_replayed_message_log_document(), load_message_log_messages(), _message_from_document_entry(), _message_to_document_entry() (+25 more)

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (24): build_parser(), _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_ids_from_replayed_messages(), process_local_inbox(), Command-line interface for the local AetherMesh prototype., Load an existing ledger and return read-only aggregate totals., Replay a saved local message log and process one node inbox. (+16 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (13): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace., Raised when a local node-state JSON file cannot be safely loaded or saved., Durable local record of assignment messages already processed by one node. (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.41
Nodes (3): _assignment(), LocalNodeServiceTests, _service()

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 0`, `Community 3`, `Community 6`, `Community 7`, `Community 12`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 1`, `Community 6`, `Community 7`, `Community 12`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Why does `process_local_inbox()` connect `Community 12` to `Community 0`, `Community 2`, `Community 5`, `Community 7`, `Community 8`, `Community 14`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `LocalMessageBus`) actually correct?**
  _`MeshMessage` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ScheduledNode` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`ScheduledNode` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _114 weakly-connected nodes found - possible documentation gaps or missing edges._