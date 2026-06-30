# Graph Report - aethermesh-core  (2026-06-30)

## Corpus Check
- 55 files · ~39,284 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 795 nodes · 2330 edges · 22 communities (20 shown, 2 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 203 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `12d97bf1`
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
- [[_COMMUNITY_Community 24|Community 24]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 131 edges
2. `JobResult` - 74 edges
3. `main()` - 72 edges
4. `MeshMessage` - 72 edges
5. `CliTests` - 56 edges
6. `NodeIdentity` - 49 edges
7. `LocalRunner` - 45 edges
8. `ContributionLedger` - 44 edges
9. `ScheduledNode` - 44 edges
10. `validate_job_result()` - 44 edges

## Surprising Connections (you probably didn't know these)
- `FlowAuditTamperTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_flow_audit.py → src/aethermesh_core/flow_audit.py
- `FlowAuditTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_flow_audit.py → src/aethermesh_core/flow_audit.py
- `QualityGateEdgeCoverageTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/identity.py
- `QualityGateEdgeCoverageTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/job_manifest.py
- `QualityGateEdgeCoverageTests` --uses--> `ContributionRecord`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/ledger.py

## Import Cycles
- None detected.

## Communities (22 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (15): _identity_document(), IdentityPersistenceError, _load_identity(), load_or_create_identity(), Local node identity persistence helpers., Raised when local identity JSON cannot be safely loaded or saved., Load a versioned local node identity, creating one if the file is missing., _save_identity() (+7 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (16): announce_local_node(), build_node_announcement_message_log_document(), build_node_heartbeat_message(), NodeAnnouncementError, normalize_announcement_capabilities(), Local-only node heartbeat announcement helpers., Build and write one local node heartbeat announcement message log., Raised when a local node announcement cannot be built or written safely. (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (30): _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Contribution ledger helpers for local job results. (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (30): InboxReplayRequest, Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), run_demo(), Return capped integer contribution units for one validated local result.      Th, score_validated_contribution(), Job, JobResult (+22 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (15): AetherMesh Core Architecture, Core responsibilities, Design principles, Growth path, Non-goals for the first prototype, Open questions, Purpose, Suggested first runnable slice (+7 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (45): _assert_assignment_matches_receipt(), _assert_contribution_message_matches_receipt(), _assert_equal(), _assert_result_message_matches_receipt(), audit_local_flow(), _find_flow_message_for_receipt(), FlowAuditError, _format_claim() (+37 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (36): Assignment-only local dispatch for manifest-backed batches., AetherMesh Core local prototype package., MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Local mesh message envelopes for deterministic simulation output., _require_non_empty_string(), _require_supported_message_type() (+28 more)

### Community 7 - "Community 7"
Cohesion: 0.14
Nodes (10): LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., Create and send a message with the next deterministic bus sequence id., send_numbered_message() (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.06
Nodes (5): build_parser(), main(), ArgumentParser, CliTests, LocalTransportCliTests

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (18): _load_inbox_document(), load_local_inbox(), local_inbox_path(), LocalTransportError, materialize_local_inboxes(), File-backed local transport inboxes for addressed mesh messages.  Version 1 loca, Return the deterministic inbox path for ``node_id``., Raised when a file-backed local transport inbox cannot be loaded or saved. (+10 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (16): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), LocalJobBatch, ManifestError, _parse_capabilities(), _parse_job_entry(), _parse_jobs() (+8 more)

### Community 14 - "Community 14"
Cohesion: 0.13
Nodes (13): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace., Raised when a local node-state JSON file cannot be safely loaded or saved., Durable local record of assignment messages already processed by one node. (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.18
Nodes (12): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Read-only local peer roster derived from heartbeat messages. (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.05
Nodes (39): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., LocalDispatchResult, Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., _message_from_inbox_entry(), build_dispatch_message_log_document(), build_flow_message_log_document() (+31 more)

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (16): CompletedProcess, Namespace, changed_pyproject_from_base(), command_artifact_provenance(), command_dependency_audit(), command_dependency_review(), command_mutation_score(), command_pr_size() (+8 more)

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (31): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _node_artifact_filename(), _node_artifact_path(), _node_ids_from_replayed_messages(), process_local_inbox(), Command-line interface for the local AetherMesh prototype., Load an existing ledger and return read-only aggregate totals. (+23 more)

### Community 19 - "Community 19"
Cohesion: 0.06
Nodes (25): dispatch_local_batch(), _node_heartbeat_payloads(), Build a local dispatch log with heartbeats and job assignments only.      This f, NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports. (+17 more)

### Community 20 - "Community 20"
Cohesion: 0.53
Nodes (8): _cap_units(), _ceil_div(), _non_negative_int(), Deterministic contribution scoring for validated local workload results., _score_keyword_extract(), _score_text_chunk(), _score_text_embed(), _score_text_stats()

### Community 24 - "Community 24"
Cohesion: 0.36
Nodes (3): _assignment(), LocalNodeServiceTests, _service()

## Knowledge Gaps
- **15 isolated node(s):** `aethermesh-core`, `AetherMesh Core Agent Notes`, `North star`, `Development approach`, `Current status` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Community 3` to `Community 5`, `Community 6`, `Community 13`, `Community 16`, `Community 18`, `Community 19`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 1`, `Community 3`, `Community 5`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 18`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 16` to `Community 1`, `Community 3`, `Community 5`, `Community 6`, `Community 7`, `Community 12`, `Community 15`, `Community 18`, `Community 24`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `Job` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`Job` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `MeshMessage` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`MeshMessage` has 22 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh-core`, `AetherMesh Core local prototype package.`, `Command-line interface for the local AetherMesh prototype.` to the rest of the system?**
  _154 weakly-connected nodes found - possible documentation gaps or missing edges._