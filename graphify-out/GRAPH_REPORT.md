# Graph Report - aethermesh-core  (2026-06-29)

## Corpus Check
- 51 files · ~30,188 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 695 nodes · 1984 edges · 30 communities (26 shown, 4 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 196 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4ed95d3d`
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
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 108 edges
2. `MeshMessage` - 71 edges
3. `main()` - 70 edges
4. `JobResult` - 61 edges
5. `CliTests` - 51 edges
6. `ScheduledNode` - 44 edges
7. `ContributionLedger` - 41 edges
8. `NodeIdentity` - 41 edges
9. `validate_job_result()` - 40 edges
10. `LocalRunner` - 37 edges

## Surprising Connections (you probably didn't know these)
- `FlowAuditTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_flow_audit.py → src/aethermesh_core/flow_audit.py
- `QualityGateEdgeCoverageTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/flow_audit.py
- `QualityGateEdgeCoverageTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/identity.py
- `QualityGateEdgeCoverageTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/job_manifest.py
- `ContributionLedgerTests` --uses--> `ContributionRecord`  [INFERRED]
  tests/test_ledger.py → src/aethermesh_core/ledger.py

## Import Cycles
- None detected.

## Communities (30 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.22
Nodes (9): _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing., _save_identity() (+1 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (16): announce_local_node(), build_node_announcement_message_log_document(), build_node_heartbeat_message(), NodeAnnouncementError, normalize_announcement_capabilities(), Local-only node heartbeat announcement helpers., Build and write one local node heartbeat announcement message log., Raised when a local node announcement cannot be built or written safely. (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.18
Nodes (8): ContributionLedger, load_existing_ledger_document(), load_ledger_document(), Load a JSON-backed local ledger, treating a missing file as empty.      The retu, Load an existing JSON-backed local ledger without creating defaults., Small in-memory ledger for prototype contribution accounting., _summary_to_simulation_dict(), ContributionLedgerTests

### Community 3 - "Community 3"
Cohesion: 0.07
Nodes (26): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), run_demo(), Job, JobResult, NodeIdentity, Identity for one local node., Create a caller-usable ephemeral identity for local demo runs. (+18 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (45): _assert_assignment_matches_receipt(), _assert_contribution_message_matches_receipt(), _assert_equal(), _assert_result_message_matches_receipt(), audit_local_flow(), _find_flow_message_for_receipt(), FlowAuditError, _format_claim() (+37 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (21): Command-line interface for the local AetherMesh prototype., Assignment-only local dispatch for manifest-backed batches., AetherMesh Core local prototype package., Shared JSON file persistence helpers for local-only artifacts., Contribution ledger helpers for local job results., MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence. (+13 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (11): send_numbered_message(), LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., Create and send a message with the next deterministic bus sequence id. (+3 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (7): build_parser(), main(), Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ArgumentParser, CliTests, LocalTransportCliTests

### Community 12 - "Community 12"
Cohesion: 0.09
Nodes (30): _load_inbox_document(), load_local_inbox(), local_inbox_path(), LocalTransportError, materialize_local_inboxes(), _message_from_inbox_entry(), File-backed local transport inboxes for addressed mesh messages.  Version 1 loca, Return the deterministic inbox path for ``node_id``. (+22 more)

### Community 13 - "Community 13"
Cohesion: 0.10
Nodes (20): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs() (+12 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (18): _fallback_job_id(), _job_from_assignment_payload(), empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace. (+10 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (12): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Read-only local peer roster derived from heartbeat messages. (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (30): _node_artifact_filename(), _node_artifact_path(), Run dispatch and all available local worker inboxes as one local flow., Return a deterministic, non-merging filename for one manifest node id., run_local_flow(), atomic_write_json(), Write one JSON document using a temp file and atomic replace., Best-effort removal for abandoned atomic-write temp files. (+22 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (7): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order., _node_heartbeat_messages(), Return deterministic local heartbeat payloads for available nodes only., NodeRegistryTests

### Community 18 - "Community 18"
Cohesion: 0.20
Nodes (12): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), InboxReplayRequest, _node_ids_from_replayed_messages(), process_local_inbox(), Replay a saved local message log or local transport inbox for one node., Replay saved local messages and return payload plus structured result., InboxProcessResult (+4 more)

### Community 19 - "Community 19"
Cohesion: 0.23
Nodes (6): _coerce_node(), LocalScheduler, Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., ScheduledNode, LocalSchedulerTests

### Community 20 - "Community 20"
Cohesion: 0.18
Nodes (9): ContributionRecord, LedgerPersistenceError, Audit record derived from one local job result., Deserialize a ledger from the local JSON file shape., Raised when a local ledger JSON file cannot be safely loaded or saved., Serialize the record into a JSON-compatible dictionary., Deserialize one JSON-compatible contribution record., _record_from_json_value() (+1 more)

### Community 21 - "Community 21"
Cohesion: 0.15
Nodes (11): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), Build a deterministic version 1 assignment-only dispatch document., JobAssignment, NoAvailableNodesError, Raised when local job assignment has jobs but no available nodes., Structured local assignment of one job to one node. (+3 more)

### Community 22 - "Community 22"
Cohesion: 0.17
Nodes (8): _accounted_units(), ContributionSummary, Record one result and return its local contribution record.          Only comple, Return deterministic aggregate totals for one local node., Return node ids present in the ledger in deterministic order., Return a deterministic JSON-compatible summary of all records., Aggregated contribution totals for one local node., _string_output()

### Community 23 - "Community 23"
Cohesion: 0.18
Nodes (5): Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., _RegistryNode

### Community 24 - "Community 24"
Cohesion: 0.41
Nodes (3): _assignment(), LocalNodeServiceTests, _service()

### Community 25 - "Community 25"
Cohesion: 0.22
Nodes (7): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., Build a local dispatch log with heartbeats and job assignments only.      This f, DispatchTests

### Community 26 - "Community 26"
Cohesion: 0.29
Nodes (5): Serialize the ledger into the small local JSON file shape., Write a JSON-backed local ledger via temp-file then atomic replace., Serialize the summary into a JSON-compatible dictionary., _remove_temp_file(), save_ledger_document()

### Community 28 - "Community 28"
Cohesion: 0.50
Nodes (3): LocalSimulationResult, Structured, deterministic output from a local multi-node simulation., Serialize the simulation result into a JSON-compatible dictionary.          Vali

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 1`, `Community 3`, `Community 5`, `Community 6`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 18`, `Community 21`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 5`, `Community 6`, `Community 13`, `Community 14`, `Community 16`, `Community 18`, `Community 19`, `Community 21`, `Community 25`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 12` to `Community 1`, `Community 5`, `Community 6`, `Community 7`, `Community 14`, `Community 15`, `Community 16`, `Community 18`, `Community 21`, `Community 24`, `Community 25`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `Job` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`Job` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `MeshMessage` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`MeshMessage` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _155 weakly-connected nodes found - possible documentation gaps or missing edges._