# Graph Report - aethermesh-core  (2026-07-01)

## Corpus Check
- 73 files · ~61,404 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1163 nodes · 3347 edges · 40 communities (34 shown, 6 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 234 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `611c4d7b`
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
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 149 edges
2. `main()` - 101 edges
3. `MeshMessage` - 97 edges
4. `JobResult` - 88 edges
5. `CliTests` - 64 edges
6. `NodeIdentity` - 53 edges
7. `ScheduledNode` - 52 edges
8. `validate_job_result()` - 51 edges
9. `LocalRunner` - 48 edges
10. `ContributionLedger` - 45 edges

## Surprising Connections (you probably didn't know these)
- `QualityGateEdgeCoverageTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/flow_audit.py
- `QualityGateEdgeCoverageTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/identity.py
- `QualityGateEdgeCoverageTests` --uses--> `ManifestError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/job_manifest.py
- `LocalNodeServiceTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_node_service.py → src/aethermesh_core/ledger.py
- `ReceiptTests` --uses--> `ContributionLedger`  [INFERRED]
  tests/test_receipts.py → src/aethermesh_core/ledger.py

## Import Cycles
- None detected.

## Communities (40 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (30): run_demo(), _default_goos(), deterministic_machine_node_id(), _fallback_parts(), _filter_empty(), _identity_document(), IdentityPersistenceError, _load_identity() (+22 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (16): announce_local_node(), build_node_announcement_message_log_document(), build_node_heartbeat_message(), NodeAnnouncementError, normalize_announcement_capabilities(), Local-only node heartbeat announcement helpers., Build and write one local node heartbeat announcement message log., Raised when a local node announcement cannot be built or written safely. (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (34): ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Return deterministic aggregate totals for one local node., Return node ids present in the ledger in deterministic order. (+26 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (45): Return capped integer contribution units for one validated local result.      Th, score_validated_contribution(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally. (+37 more)

### Community 4 - "Community 4"
Cohesion: 0.22
Nodes (9): AetherMesh Core, Architecture, Architecture direction, Current status, Development approach, Installable CLI and local UI, Near-term build direction, North star (+1 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (20): _assignment_key(), _job_from_assignment(), LocalValidationError, Independent local replay validation for reported AetherMesh job results., Normalize credited local result messages back to runner-result shape.      Worke, Raised when local validation replay cannot safely produce an artifact., Replay assignment/result logs and write an independent validation report., _required_non_empty_string() (+12 more)

### Community 6 - "Community 6"
Cohesion: 0.08
Nodes (29): Assignment-only local dispatch for manifest-backed batches., AetherMesh Core local prototype package., _accounted_units(), Contribution ledger helpers for local job results., Record one result and return its local contribution record.          Only comple, _string_output(), MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation. (+21 more)

### Community 7 - "Community 7"
Cohesion: 0.08
Nodes (21): LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., Create and send a message with the next deterministic bus sequence id., send_numbered_message() (+13 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (24): init(), jobs(), main(), node_start(), node_status(), peers(), _print_status(), First-class AetherMesh CLI for local node, API, and UI workflows. (+16 more)

### Community 12 - "Community 12"
Cohesion: 0.11
Nodes (32): collect_local_outboxes(), _load_inbox_document(), load_local_inbox(), _load_outbox_document(), local_inbox_path(), local_outbox_path(), LocalTransportError, materialize_local_inboxes() (+24 more)

### Community 13 - "Community 13"
Cohesion: 0.09
Nodes (21): dispatch_local_batch_command(), Run a local simulation from a validated JSON manifest., Dispatch a manifest batch to a local message log without execution., run_local_batch(), load_job_manifest(), _load_manifest_document(), load_manifest_jobs(), LocalJobBatch (+13 more)

### Community 14 - "Community 14"
Cohesion: 0.08
Nodes (32): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), InboxReplayRequest, _node_artifact_filename(), _node_artifact_path(), _node_ids_from_replayed_messages(), process_local_inbox(), Command-line interface for the local AetherMesh prototype. (+24 more)

### Community 15 - "Community 15"
Cohesion: 0.13
Nodes (16): dispatch_peer_batch_command(), Dispatch manifest jobs to heartbeat-derived peers without execution., Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError (+8 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (18): build_collected_outbox_message_log_document(), build_dispatch_message_log_document(), build_message_log_document(), build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages(), load_worker_emitted_messages(), _message_to_document_entry() (+10 more)

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (16): CompletedProcess, Namespace, changed_pyproject_from_base(), command_artifact_provenance(), command_dependency_audit(), command_dependency_review(), command_mutation_score(), command_pr_size() (+8 more)

### Community 18 - "Community 18"
Cohesion: 0.05
Nodes (64): _accepted_result(), aggregate_local_flow(), AggregationError, build_local_flow_aggregate(), _is_accepted(), Deterministic local aggregation for completed flow artifact directories., Raised when a local flow aggregate cannot be built or written safely., Build a deterministic aggregate document after auditing a flow directory. (+56 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (14): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order. (+6 more)

### Community 20 - "Community 20"
Cohesion: 0.05
Nodes (44): create_app(), _lifespan(), Local FastAPI app for the AetherMesh node dashboard., Create the localhost API/dashboard app used by CLI and UI frontends., _cap_units(), _ceil_div(), _non_negative_int(), Deterministic contribution scoring for validated local workload results. (+36 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (9): build_flow_message_log_document(), _message_from_document_entry(), Build a deterministic version 1 run-level local flow message log., MeshMessage, message_from_mapping(), JSON-compatible message envelope for local mesh communication records., Serialize the message into a JSON-compatible dictionary., Build a validated MeshMessage from a JSON-like mapping. (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.21
Nodes (6): _coerce_node(), LocalScheduler, Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., ScheduledNode, LocalSchedulerTests

### Community 23 - "Community 23"
Cohesion: 0.20
Nodes (17): build_parser(), format_duration(), format_progress_line(), main(), max_non_killed_for_score(), parse_mutmut_counts(), parse_mutmut_progress(), Return latest mutmut progress counters from text. (+9 more)

### Community 24 - "Community 24"
Cohesion: 0.19
Nodes (5): Run local jobs across local node identities using scheduler assignment.      Thi, run_local_simulation(), _summary_to_simulation_dict(), _validation_summary(), LocalSimulationTests

### Community 25 - "Community 25"
Cohesion: 0.30
Nodes (14): _base_checks(), build_parser(), Check, _checks_for_mode(), _command_available(), _full_extra_checks(), main(), _merged_env() (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (14): AetherMesh Core Persistent Goal, AI Direction, Build Direction, Contribution Tracking Direction, Current Priority Bias, Decision Rule For Every Interval, Development Philosophy, Early Prototype Target (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (12): AEF: Aether Expert Fabric, AER: Adaptive Expert Routing, AetherMesh Core Architecture, Contribution tracking direction, Core responsibilities, Current prototype layer, Decision rule for new work, Non-goals for the current prototype (+4 more)

### Community 28 - "Community 28"
Cohesion: 0.18
Nodes (9): LocalDispatchResult, Structured result for local assignment-only dispatch., JobAssignment, Structured local assignment of one job to one node., Serialize the assignment into a JSON-compatible dictionary., Assign jobs to available capable nodes with deterministic fair ordering., LocalSimulationResult, _node_roster_entry() (+1 more)

### Community 29 - "Community 29"
Cohesion: 0.31
Nodes (4): dispatch_local_batch(), _node_heartbeat_payloads(), Build a local dispatch log with heartbeats and job assignments only.      This f, DispatchTests

### Community 30 - "Community 30"
Cohesion: 0.27
Nodes (6): atomic_write_json(), Shared JSON file persistence helpers for local-only artifacts., Write one JSON document using a temp file and atomic replace., Best-effort removal for abandoned atomic-write temp files., remove_temp_file(), JsonIoTests

### Community 31 - "Community 31"
Cohesion: 0.36
Nodes (3): ModuleType, FullTestRunnerTests, load_full_test_module()

### Community 32 - "Community 32"
Cohesion: 0.25
Nodes (8): AEF — Aether Expert Fabric, AER — Adaptive Expert Routing, Aggregator, Core Terms, Expert, REVA Pipeline, Router, Validator

### Community 33 - "Community 33"
Cohesion: 0.25
Nodes (8): CLI and Local UI Architecture, Commands, Future Tauri desktop path, Install, Local API, Local dashboard, Security default, Shape

### Community 35 - "Community 35"
Cohesion: 0.40
Nodes (5): Aggregator, Expert, REVA pipeline, Router, Validator

## Knowledge Gaps
- **51 isolated node(s):** `aethermesh`, `PR validation gates`, `North star`, `Architecture direction`, `Development approach` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Community 3` to `Community 0`, `Community 2`, `Community 37`, `Community 5`, `Community 6`, `Community 7`, `Community 13`, `Community 14`, `Community 16`, `Community 22`, `Community 24`, `Community 28`, `Community 29`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `MeshMessage` connect `Community 21` to `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 6`, `Community 7`, `Community 8`, `Community 12`, `Community 14`, `Community 15`, `Community 16`, `Community 18`, `Community 28`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 0`, `Community 1`, `Community 34`, `Community 37`, `Community 38`, `Community 5`, `Community 12`, `Community 13`, `Community 14`, `Community 15`, `Community 18`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 21 inferred relationships involving `Job` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`Job` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Path` (e.g. with `.test_run_demo_malformed_ledger_path_returns_cli_error()` and `.test_run_demo_persists_json_ledger_and_accumulates_summary()`) actually correct?**
  _`Path` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `MeshMessage` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`MeshMessage` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aethermesh`, `One validation command to run.`, `Return latest mutmut progress counters from text.` to the rest of the system?**
  _240 weakly-connected nodes found - possible documentation gaps or missing edges._