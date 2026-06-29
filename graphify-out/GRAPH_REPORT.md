# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 38 files · ~20,138 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 498 nodes · 1280 edges · 21 communities (17 shown, 4 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 131 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c84991c2`
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

## God Nodes (most connected - your core abstractions)
1. `Job` - 67 edges
2. `main()` - 54 edges
3. `CliTests` - 46 edges
4. `MeshMessage` - 44 edges
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

## Communities (21 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.21
Nodes (10): _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing., _remove_temp_file() (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (10): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order., _node_heartbeat_messages() (+2 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (47): build_parser(), _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_artifact_filename(), _node_artifact_path(), _node_ids_from_replayed_messages(), process_local_inbox(), Command-line interface for the local AetherMesh prototype. (+39 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (33): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), run_demo(), Job, JobResult, NodeIdentity, Identity for one local node., Create a caller-usable ephemeral identity for local demo runs. (+25 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (11): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+3 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (25): Run a local simulation from a validated JSON manifest., run_local_batch(), Serialize a deterministic, intentionally small CLI summary., load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry() (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (20): build_flow_message_log_document(), build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages(), load_worker_emitted_messages(), _message_from_document_entry(), MessageLogPersistenceError, JSON-backed local message log persistence for batch simulations. (+12 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (15): AetherMesh Core local prototype package., Local mesh message envelopes for deterministic simulation output., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible(), Core data models for the local AetherMesh prototype., _fallback_job_id(), _job_from_assignment_payload() (+7 more)

### Community 14 - "Community 14"
Cohesion: 0.14
Nodes (13): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace., Raised when a local node-state JSON file cannot be safely loaded or saved., Durable local record of assignment messages already processed by one node. (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.17
Nodes (9): Deterministic local node registry for simulation roster state., Register a node ID or ScheduledNode in deterministic insertion order., _RegistryNode, NodeStatus, _normalize_capabilities(), Deterministic local scheduler for the AetherMesh prototype., Availability states needed by the local scheduler., Enum (+1 more)

### Community 16 - "Community 16"
Cohesion: 0.27
Nodes (6): _coerce_node(), LocalScheduler, Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., ScheduledNode, LocalSchedulerTests

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (8): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Assignment-only local dispatch for manifest-backed batches., Structured result for local assignment-only dispatch., Build a local dispatch log with heartbeats and job assignments only.      This f, _send_dispatch_message(), DispatchTests

### Community 18 - "Community 18"
Cohesion: 0.41
Nodes (3): _assignment(), LocalNodeServiceTests, _service()

### Community 19 - "Community 19"
Cohesion: 0.22
Nodes (8): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), Build a deterministic version 1 assignment-only dispatch document., JobAssignment, Structured local assignment of one job to one node., Serialize the assignment into a JSON-compatible dictionary., _node_roster_entry()

### Community 20 - "Community 20"
Cohesion: 0.29
Nodes (6): _coerce_job(), NoAvailableNodesError, Raised when local job assignment has jobs but no available nodes., Minimal scheduler view of a job., Assign jobs round-robin across available capable nodes in input order., ScheduledJob

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 3`, `Community 2`, `Community 19`, `Community 6`?**
  _High betweenness centrality (0.159) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 2`, `Community 6`, `Community 7`, `Community 12`, `Community 16`, `Community 17`, `Community 19`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 7` to `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 12`, `Community 17`, `Community 18`, `Community 19`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `Job` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`Job` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `MeshMessage` (e.g. with `LocalDispatchResult` and `LocalMessageBus`) actually correct?**
  _`MeshMessage` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ScheduledNode` (e.g. with `LocalDispatchResult` and `LocalJobBatch`) actually correct?**
  _`ScheduledNode` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _118 weakly-connected nodes found - possible documentation gaps or missing edges._