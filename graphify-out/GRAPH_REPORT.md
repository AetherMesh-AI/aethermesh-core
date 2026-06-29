# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 38 files · ~19,526 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 491 nodes · 1250 edges · 20 communities (17 shown, 3 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 131 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bf25c15b`
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
1. `Job` - 67 edges
2. `main()` - 54 edges
3. `CliTests` - 46 edges
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
- `MessageLogTests` --uses--> `MeshMessage`  [INFERRED]
  tests/test_message_log.py → src/aethermesh_core/messages.py
- `LocalNodeServiceTests` --uses--> `NodeIdentity`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/models.py
- `DispatchTests` --uses--> `Job`  [INFERRED]
  tests/test_dispatch.py → src/aethermesh_core/models.py

## Import Cycles
- None detected.

## Communities (20 total, 3 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (17): run_demo(), _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing. (+9 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (8): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order., NodeRegistryTests

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (32): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary (+24 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (19): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., build_text_stats_output(), Run one local job and return a structured result. (+11 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (22): LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., MeshMessage, JSON-compatible message envelope for local mesh communication records. (+14 more)

### Community 6 - "Community 6"
Cohesion: 0.11
Nodes (21): Run a local simulation from a validated JSON manifest., run_local_batch(), Serialize a deterministic, intentionally small CLI summary., load_job_manifest(), ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs() (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (23): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), build_message_log_document(), build_replayed_message_log_document(), load_message_log_messages(), _message_from_document_entry(), _message_to_document_entry() (+15 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (4): build_parser(), main(), ArgumentParser, CliTests

### Community 12 - "Community 12"
Cohesion: 0.15
Nodes (14): Command-line interface for the local AetherMesh prototype., AetherMesh Core local prototype package., Contribution ledger helpers for local job results., MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Local mesh message envelopes for deterministic simulation output., Core data models for the local AetherMesh prototype. (+6 more)

### Community 14 - "Community 14"
Cohesion: 0.09
Nodes (27): _node_artifact_filename(), _node_artifact_path(), _node_ids_from_replayed_messages(), process_local_inbox(), Run dispatch and all available local worker inboxes as one local flow., Return a deterministic, non-merging filename for one manifest node id., Replay a saved local message log and process one node inbox., run_local_flow() (+19 more)

### Community 15 - "Community 15"
Cohesion: 0.15
Nodes (9): Deterministic local node registry for simulation roster state., _coerce_job(), NoAvailableNodesError, _normalize_capabilities(), Deterministic local scheduler for the AetherMesh prototype., Raised when local job assignment has jobs but no available nodes., Minimal scheduler view of a job., Assign jobs round-robin across available capable nodes in input order. (+1 more)

### Community 16 - "Community 16"
Cohesion: 0.27
Nodes (6): _coerce_node(), LocalScheduler, Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., ScheduledNode, LocalSchedulerTests

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (8): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Assignment-only local dispatch for manifest-backed batches., Structured result for local assignment-only dispatch., Build a local dispatch log with heartbeats and job assignments only.      This f, _send_dispatch_message(), DispatchTests

### Community 18 - "Community 18"
Cohesion: 0.22
Nodes (8): Register a node ID or ScheduledNode in deterministic insertion order., _RegistryNode, NodeStatus, Availability states needed by the local scheduler., LocalSimulationResult, Structured, deterministic output from a local multi-node simulation., Enum, str

### Community 19 - "Community 19"
Cohesion: 0.50
Nodes (3): LocalJobBatch, Validated local batch inputs for the local simulation path., Return manifest node IDs in deterministic manifest order.

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 0`, `Community 2`, `Community 3`, `Community 6`, `Community 7`, `Community 12`, `Community 14`?**
  _High betweenness centrality (0.161) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 0`, `Community 2`, `Community 5`, `Community 6`, `Community 7`, `Community 12`, `Community 16`, `Community 17`, `Community 18`, `Community 19`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Why does `process_local_inbox()` connect `Community 14` to `Community 0`, `Community 2`, `Community 5`, `Community 7`, `Community 8`, `Community 12`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `LocalMessageBus`) actually correct?**
  _`MeshMessage` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ScheduledNode` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`ScheduledNode` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _116 weakly-connected nodes found - possible documentation gaps or missing edges._