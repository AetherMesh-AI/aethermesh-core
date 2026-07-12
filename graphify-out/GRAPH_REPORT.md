# Graph Report - aethermesh-core  (2026-07-11)

## Corpus Check
- 136 files · ~180,809 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2196 nodes · 5916 edges · 103 communities (88 shown, 15 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 399 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `59c2bd86`
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
- [[_COMMUNITY_Community 11|Community 11]]
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
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_models.py|models.py]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_release_update.py|release_update.py]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Desktop Troubleshooting|Desktop Troubleshooting]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_REVA Pipeline|REVA Pipeline]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 155 edges
2. `main()` - 120 edges
3. `main()` - 97 edges
4. `MeshMessage` - 97 edges
5. `JobResult` - 89 edges
6. `NodeIdentity` - 80 edges
7. `IdentityPersistenceTests` - 73 edges
8. `CliTests` - 72 edges
9. `start_local_node()` - 67 edges
10. `LocalRunner` - 53 edges

## Surprising Connections (you probably didn't know these)
- `QualityGateEdgeCoverageTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/flow_audit.py
- `IdentityPersistenceTests` --uses--> `HardwareIdentityInputs`  [INFERRED]
  tests/test_identity.py → src/aethermesh_core/identity.py
- `IdentityPersistenceTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_identity.py → src/aethermesh_core/identity.py
- `QualityGateEdgeCoverageTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/identity.py
- `VersionMetadataTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_version_metadata.py → src/aethermesh_core/identity.py

## Import Cycles
- None detected.

## Communities (103 total, 15 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (5): NodeIdentity, Identity for one local node., LocalRunner, Execute supported local job types for a node., LocalRunnerTests

### Community 1 - "Community 1"
Cohesion: 0.15
Nodes (16): announce_local_node(), build_node_announcement_message_log_document(), build_node_heartbeat_message(), NodeAnnouncementError, normalize_announcement_capabilities(), Local-only node heartbeat announcement helpers., Build and write one local node heartbeat announcement message log., Raised when a local node announcement cannot be built or written safely. (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (32): collect_local_outboxes(), _load_inbox_document(), load_local_inbox(), _load_outbox_document(), local_inbox_path(), local_outbox_path(), LocalTransportError, materialize_local_inboxes() (+24 more)

### Community 3 - "Community 3"
Cohesion: 0.15
Nodes (6): JobResult, Structured result emitted after local job execution., _invalid(), Validate a reported result against the assigned local job.      The current prot, validate_job_result(), ValidationTests

### Community 4 - "Community 4"
Cohesion: 0.20
Nodes (10): AetherMesh Core, Current status, Development principles, Documentation, Install for development, License, Prototype flow examples, Quick start (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (20): _assignment_key(), _job_from_assignment(), LocalValidationError, Independent local replay validation for reported AetherMesh job results., Normalize credited local result messages back to runner-result shape.      Worke, Raised when local validation replay cannot safely produce an artifact., Replay assignment/result logs and write an independent validation report., _required_non_empty_string() (+12 more)

### Community 6 - "Community 6"
Cohesion: 0.22
Nodes (8): dispatch_local_batch_command(), Dispatch a manifest batch to a local message log without execution., build_dispatch_message_log_document(), Build a deterministic version 1 assignment-only dispatch document., JobAssignment, Structured local assignment of one job to one node., Serialize the assignment into a JSON-compatible dictionary., _node_roster_entry()

### Community 7 - "Community 7"
Cohesion: 0.06
Nodes (32): shouldLeaveBackgroundNodeRunning(), shouldStopTemporaryNode(), fs, getBundledRuntimePath(), getRuntimeExecutableName(), path, resolveRuntimeCommand(), getAetherMeshPaths() (+24 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (3): main(), main(), CliTests

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (49): _background_mode_enabled(), _control_background_node(), init(), jobs(), _local_api_is_aethermesh(), main(), node_start(), node_status() (+41 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (30): _bytes_to_gb(), collect_hardware_identity_inputs(), _colon_value(), _count_display_chips(), _csv_first_value(), _darwin_hardware_inputs(), _extract_mac_addresses(), _linux_cpu_value() (+22 more)

### Community 12 - "Community 12"
Cohesion: 0.36
Nodes (23): backgroundStateFromSettings(), bootstrap(), checkRuntimeUpdates(), cliStateFromSettings(), createBackgroundManager(), createCliManager(), disableBackgroundNode(), enableBackgroundNode() (+15 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (26): CapabilityRecordError, Validation for the local-only version 1 capability record contract., Raised when a local capability record is incomplete or dishonest., Validate and return one local-only capability record without writing it.      A, _require_attribution(), _require_identifier(), _require_identifier_list(), _require_int() (+18 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (68): _accepted_result(), aggregate_local_flow(), AggregationError, build_local_flow_aggregate(), _is_accepted(), Deterministic local aggregation for completed flow artifact directories., Raised when a local flow aggregate cannot be built or written safely., Build a deterministic aggregate document after auditing a flow directory. (+60 more)

### Community 15 - "Community 15"
Cohesion: 0.10
Nodes (15): BackgroundNodeManager, buildLaunchAgentPlist(), buildSystemdUserService(), buildWindowsTaskXml(), crypto, { execFile: defaultExecFile }, execFilePromise(), fs (+7 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (10): build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages(), load_worker_emitted_messages(), MessageLogPersistenceError, Raised when a local message log JSON file cannot be safely loaded or saved., Load validated MeshMessage entries from a version 1 local message log.      The, Load only post-replay worker-emitted messages from a worker message log. (+2 more)

### Community 17 - "Community 17"
Cohesion: 0.28
Nodes (17): CompletedProcess, Namespace, changed_pyproject_from_base(), command_artifact_provenance(), command_dependency_audit(), command_dependency_review(), command_mutation_score(), command_pr_size() (+9 more)

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (33): configured_runtime_path(), configured_runtime_ref(), default_local_runtime_config(), load_local_runtime_config(), load_optional_local_runtime_config(), load_or_create_local_runtime_config(), LocalRuntimeConfig, LocalRuntimeConfigError (+25 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (13): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order. (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.28
Nodes (16): build_parser(), build_release_metadata(), command_prepare(), Commit, commits_since(), format_release_notes(), head_sha(), main() (+8 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (19): buildPosixShim(), buildShellPathBlock(), buildWindowsCmdShim(), buildWindowsPowerShellShim(), CliManager, { execFile: defaultExecFile }, execFilePromise(), fs (+11 more)

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (10): _coerce_node(), LocalScheduler, NoAvailableNodesError, _normalize_capabilities(), Raised when local job assignment has jobs but no available nodes., Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., Assign jobs to available capable nodes with deterministic fair ordering. (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.10
Nodes (24): ModuleType, RuntimeError, build_parser(), format_duration(), format_progress_line(), main(), max_non_killed_for_score(), parse_mutmut_counts() (+16 more)

### Community 24 - "Community 24"
Cohesion: 0.18
Nodes (11): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), build_message_log_document(), Build a deterministic version 1 audit document for local mesh messages., Job, A small in-memory job assigned to a local node., LocalSimulationResult, Structured, deterministic output from a local multi-node simulation. (+3 more)

### Community 25 - "Community 25"
Cohesion: 0.15
Nodes (14): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Read-only local peer roster derived from heartbeat messages. (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (14): AetherMesh Core Persistent Goal, AI Direction, Build Direction, Contribution Tracking Direction, Current Priority Bias, Decision Rule For Every Interval, Development Philosophy, Early Prototype Target (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (21): run_demo(), _canonical_root_json(), _component_hashes(), deterministic_machine_node_id(), deterministic_machine_node_name(), HardwareComponentHashes, HardwareIdentityInputs, _index_from_hash() (+13 more)

### Community 28 - "Community 28"
Cohesion: 0.23
Nodes (6): build_receipt_document(), Write a receipt document via temp-file then atomic replace., Build a deterministic version 1 receipt document.      Receipts are derived from, write_receipt_document(), _processed_assignment(), ReceiptTests

### Community 30 - "Community 30"
Cohesion: 0.25
Nodes (7): atomic_write_json(), _publish_json(), Shared JSON file persistence helpers for local-only artifacts., Write one JSON document using a temp file and atomic replace., Best-effort removal for abandoned atomic-write temp files., remove_temp_file(), JsonIoTests

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (13): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace., Raised when a local node-state JSON file cannot be safely loaded or saved., Durable local record of assignment messages already processed by one node. (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.09
Nodes (33): _json_compatible_dict(), _json_compatible_list(), _json_compatible_value(), load_receipt_document_if_exists(), _output_summary(), Deterministic local work receipt documents for processed jobs., Raised when a local receipt document cannot be safely loaded or saved., Return validated metadata documents keyed by their stable reference. (+25 more)

### Community 33 - "Community 33"
Cohesion: 0.25
Nodes (8): CLI and Local UI Architecture, Commands, Desktop launcher, Install, Local API, Local dashboard, Security default, Shape

### Community 34 - "Community 34"
Cohesion: 0.47
Nodes (3): build_parser(), ArgumentParser, build_parser()

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (28): _classify_startup_error(), _configured_path(), _contains_runtime_artifacts(), _default_manifest_document(), _document_hash(), _ensure_manifest_directories(), _ensure_runtime_dirs(), _identity_creator_node_id() (+20 more)

### Community 36 - "Community 36"
Cohesion: 0.10
Nodes (24): isDestroyedElectronObject(), isDestroyedError(), sendWindowState(), platformNotes(), apiClient, { app, BrowserWindow, ipcMain }, appendBootstrapLog(), assertPortAvailableForAetherMesh() (+16 more)

### Community 37 - "Community 37"
Cohesion: 0.08
Nodes (13): _identity_document(), load_or_create_identity(), parse_local_node_identity_document(), Parse and validate the Phase 1 public local node identity shape., Load a versioned local node identity, creating one if the file is missing., Explicitly replace a persisted local identity after quarantining the old one., reset_identity(), _save_identity() (+5 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (19): Local API error envelope, Local Contribution Lookup v1, Local Job Status v1, Local Job Submission v1, Local Validation Receipt v1, Phase 1 API Schema Contract, Route index, Validation receipt (+11 more)

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (25): allowed_next_states(), canonical_lifecycle_states(), LifecycleRecord, LifecycleStateSpec, LifecycleTransitionError, LocalNodeLifecycleState, Local-first lifecycle model for one AetherMesh node runtime., Canonical local node lifecycle states. (+17 more)

### Community 41 - "Community 41"
Cohesion: 0.47
Nodes (9): _cap_units(), _ceil_div(), _non_negative_int(), Deterministic contribution scoring for validated local workload results., _score_keyword_extract(), _score_text_chunk(), _score_text_embed(), _score_text_retrieve() (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (27): append_json_line(), load_json_mapping(), Small JSON helpers shared by local lifecycle commands., Read a required JSON object and raise the caller's local error type., Return a non-empty string field or raise the caller's local error type., Append one deterministic JSONL entry to a local lifecycle log., require_text_field(), _append_log() (+19 more)

### Community 43 - "Community 43"
Cohesion: 0.13
Nodes (12): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+4 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (28): _run_json_command(), canonical_json_hash(), Hash a JSON object in stable key order for local receipts., _append_log(), _artifact_refs(), _document_hash(), _interrupted_work_refs(), _iter_files() (+20 more)

### Community 45 - "Community 45"
Cohesion: 0.11
Nodes (30): _artifact_refs(), _attribution_id(), _error_summary(), inspect_local_node_runtime(), _lineage_parent(), _load_identity_and_manifest(), _load_latest_artifact(), _load_runtime_json() (+22 more)

### Community 46 - "Community 46"
Cohesion: 0.07
Nodes (31): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), InboxReplayRequest, _mark_ephemeral_message_log(), _node_ids_from_replayed_messages(), process_local_inbox(), Replay a saved local message log or local transport inbox for one node., Replay saved local messages and return payload plus structured result. (+23 more)

### Community 47 - "Community 47"
Cohesion: 0.13
Nodes (20): Run a local simulation from a validated JSON manifest., Run local file transport with workers discovered from heartbeat peers., run_local_batch(), run_peer_transport_flow(), load_job_manifest(), _load_manifest_document(), load_manifest_jobs(), LocalJobBatch (+12 more)

### Community 48 - "models.py"
Cohesion: 0.18
Nodes (10): AetherMesh Core local prototype package., Contribution ledger helpers for local job results., Core data models for the local AetherMesh prototype., Local-only node inbox processing service for assigned work messages., Canonical SHA-256 hashing for accounted local job results., build_text_retrieve_output(), Local in-memory runner for the first AetherMesh executable slice., Build deterministic token-overlap rankings for ``text_retrieve`` jobs. (+2 more)

### Community 49 - "Community 49"
Cohesion: 0.38
Nodes (4): _backup_identity_referenced_artifacts(), _local_identity_ref_path(), _string_list_from_section(), _unique_reset_artifact_path()

### Community 51 - "Community 51"
Cohesion: 0.29
Nodes (6): Conditional validation fields, Local Capability Record Schema, Optional lineage fields, Required fields, Valid passed record, Valid unvalidated record

### Community 52 - "Community 52"
Cohesion: 0.10
Nodes (19): author, description, devDependencies, electron, electron-builder, main, name, private (+11 more)

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (19): atomic_create_json(), Create one JSON document atomically without replacing an existing file., NodeRuntimeService, Raised when local runtime state cannot be safely loaded or written., Raised when a requested local validation receipt is not stored., Run a queued local submission; this is not a daemon or remote boundary., Central service for local node config, lifecycle status, peers, and jobs., Allow readable local identifiers while rejecting path and URI-shaped values. (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.11
Nodes (36): _append_identity_reset_receipt(), _contains_secret_identity_fragment(), _create_identity_document_without_overwrite(), _gpu_input(), _identity_artifact_has_identity_metadata(), _identity_artifact_mentions_node(), _identity_document_creator_node_id(), _identity_reset_artifact_ref() (+28 more)

### Community 56 - "Community 56"
Cohesion: 0.07
Nodes (25): ContributionLedger, ContributionRecord, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Small in-memory ledger for prototype contribution accounting., Audit record derived from one local job result., Serialize the ledger into the small local JSON file shape. (+17 more)

### Community 57 - "Community 57"
Cohesion: 0.11
Nodes (14): _message_from_inbox_entry(), Return a copy of the deterministic inbox for a registered node., build_collected_outbox_message_log_document(), build_flow_message_log_document(), _message_from_document_entry(), _message_to_document_entry(), Build a deterministic version 1 run-level local flow message log., Build a deterministic version 1 log from collected local transport outboxes. (+6 more)

### Community 58 - "release_update.py"
Cohesion: 0.10
Nodes (21): _config_api_host(), _config_api_port(), _config_enabled_work_types(), _config_identity_path(), _config_identity_persistence_enabled(), _config_node_id(), _config_node_name(), _default_home() (+13 more)

### Community 59 - "Community 59"
Cohesion: 0.10
Nodes (19): AER — Adaptive Expert Routing, AetherMesh Core, AetherMesh Core Persistent Goal, ai/local-loop-20260702-072353-1, Architecture direction, Core Terms, Development approach, docs/persistent-goal.md excerpt (+11 more)

### Community 60 - "Community 60"
Cohesion: 0.10
Nodes (19): AER — Adaptive Expert Routing, AetherMesh Core, AetherMesh Core Persistent Goal, ai/local-loop-20260702-072353-1, Architecture direction, Core Terms, Development approach, docs/persistent-goal.md excerpt (+11 more)

### Community 61 - "Community 61"
Cohesion: 0.14
Nodes (14): AetherMesh CLI, AetherMesh Desktop, Background OS-managed mode, Deferred work, Development commands, Manual validation, Packaging targets, Runtime model (+6 more)

### Community 62 - "Community 62"
Cohesion: 0.35
Nodes (12): _base_checks(), Check, _checks_for_mode(), _command_available(), _full_extra_checks(), _merged_env(), _missing_required_tools(), _python() (+4 more)

### Community 64 - "Community 64"
Cohesion: 0.29
Nodes (11): bootstrapState, els, formatBool(), refreshDashboard(), renderBackground(), renderCapabilities(), renderCli(), renderPeers() (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.17
Nodes (12): AEF: Aether Expert Fabric, AER: Adaptive Expert Routing, AetherMesh Core Architecture, Contribution tracking direction, Core responsibilities, Current prototype layer, Decision rule for new work, Non-goals for the current prototype (+4 more)

### Community 66 - "Community 66"
Cohesion: 0.35
Nodes (4): Return capped integer contribution units for one validated local result.      Th, score_validated_contribution(), ContributionScoringTests, _run()

### Community 67 - "Desktop Troubleshooting"
Cohesion: 0.17
Nodes (11): AetherMesh CLI, CLI shim paths, Linux, macOS, Manual tests, PATH setup, Repair CLI, Runtime updates (+3 more)

### Community 68 - "Community 68"
Cohesion: 0.11
Nodes (6): create_app(), Create the localhost API/dashboard app used by CLI and UI frontends., ApiErrorTests, AuditInspectionTests, ModelManifestInspectionTests, RuntimeServiceTests

### Community 69 - "Community 69"
Cohesion: 0.18
Nodes (10): API did not start, Bundled runtime missing, Desktop Troubleshooting, Development fallback, Linux `.deb` package metadata, Linux system dependency missing, macOS Gatekeeper, Node already running (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.18
Nodes (10): args, built, entry, fs, nodeNameWordlists, path, result, root (+2 more)

### Community 73 - "Community 73"
Cohesion: 0.14
Nodes (10): _ephemeral_roster(), _log_ephemeral_identity_active(), _mark_ephemeral_artifact(), _node_artifact_filename(), _node_artifact_path(), Command-line interface for the local AetherMesh prototype., Return a deterministic, non-merging filename for one manifest node id., _use_ephemeral_identity() (+2 more)

### Community 74 - "REVA Pipeline"
Cohesion: 0.25
Nodes (8): AEF — Aether Expert Fabric, AER — Adaptive Expert Routing, Aggregator, Core Terms, Expert, REVA Pipeline, Router, Validator

### Community 75 - "Community 75"
Cohesion: 0.17
Nodes (9): dispatch_peer_batch_command(), Dispatch manifest jobs to heartbeat-derived peers without execution., dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., Build a local dispatch log with heartbeats and job assignments only.      This f (+1 more)

### Community 76 - "Community 76"
Cohesion: 0.36
Nodes (3): _assignment(), LocalNodeServiceTests, _service()

### Community 77 - "Community 77"
Cohesion: 0.39
Nodes (7): detectPython(), { execFile }, execFileAsync, isUsablePythonVersion(), parsePythonVersion(), { promisify }, runVersion()

### Community 78 - "Community 78"
Cohesion: 0.25
Nodes (7): Local Node Identity Format, Local prototype reset procedure, Manifest linkage, Minimal example, Private key material, Version 1 document shape, Versioning rules

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (6): AetherMesh alignment, Follow-ups, Objective, Safety notes, Validation, What changed

### Community 81 - "Community 81"
Cohesion: 0.29
Nodes (6): Background Node Manual Test Plan, Linux systemd user service, macOS LaunchAgent, Runtime update checks, Shared checks, Windows Task Scheduler

### Community 83 - "Community 83"
Cohesion: 0.40
Nodes (5): Aggregator, Expert, REVA pipeline, Router, Validator

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (6): Canonical states, Local Node Lifecycle, Persisted fields for lifecycle-changing events, Restart recovery, Scope boundaries, Transition events and validation conditions

### Community 85 - "Community 85"
Cohesion: 0.47
Nodes (5): buildPackageInstallCommand(), DEFAULT_SETTINGS, normalizePackageSettings(), defaultSettings(), normalizeSettings()

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (5): fs, path, root, target, targetDir

### Community 87 - "Community 87"
Cohesion: 0.24
Nodes (11): _darwin_physical_mac_addresses(), _extract_labeled_value(), _is_darwin_physical_ethernet_or_wifi_port(), _is_physical_ethernet_or_wifi_name(), _is_physical_linux_network_interface(), _is_usable_mac_address(), _is_virtual_or_non_hardware_network_name(), _linux_physical_mac_addresses() (+3 more)

### Community 88 - "Community 88"
Cohesion: 0.40
Nodes (4): main, name, private, version

### Community 89 - "Community 89"
Cohesion: 0.18
Nodes (8): Assignment-only local dispatch for manifest-backed batches., JSON-backed local message log persistence for batch simulations., Local mesh message envelopes for deterministic simulation output., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible(), Deterministic local node registry for simulation roster state., Deterministic local scheduler for the AetherMesh prototype.

### Community 92 - "Community 92"
Cohesion: 0.50
Nodes (3): IdentityResetResult, Local audit details for an explicit identity reset., Return JSON-serializable reset details for CLI/API callers.

### Community 94 - "Community 94"
Cohesion: 0.50
Nodes (4): build_text_chunk_output(), _preferred_text_chunk_split(), Build stable character chunks for a local ``text_chunk`` job., Return a deterministic split point no later than ``hard_end``.

### Community 96 - "Community 96"
Cohesion: 0.20
Nodes (6): ContributionSummary, Serialize the summary into a JSON-compatible dictionary., Return deterministic aggregate totals for one local node., Return node ids present in the ledger in deterministic order., Return a deterministic JSON-compatible summary of all records., Aggregated contribution totals for one local node.

### Community 98 - "Community 98"
Cohesion: 0.50
Nodes (3): LocalNodeIdentity, Validated version 1 public local node identity document., Return the public identity document without private key material.

### Community 99 - "Community 99"
Cohesion: 0.40
Nodes (3): build_text_stats_output(), Build deterministic text statistics for a local ``text_stats`` job., Run one local job and return a structured result.

### Community 101 - "Community 101"
Cohesion: 0.15
Nodes (13): _error_response(), _lifespan(), Local FastAPI app for the AetherMesh node dashboard., Return the stable, deliberately non-provenance API error envelope., Classify expected local runtime failures without exposing their text., _request_id(), _runtime_error_code(), FastAPI (+5 more)

## Knowledge Gaps
- **248 isolated node(s):** `name`, `version`, `private`, `main`, `{ spawnSync }` (+243 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NodeIdentity` connect `Community 0` to `Community 32`, `Community 98`, `Community 66`, `Community 37`, `Community 71`, `Community 73`, `Community 76`, `Community 46`, `models.py`, `Community 53`, `Community 54`, `Community 24`, `release_update.py`, `Community 27`, `Community 92`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 8` to `Community 1`, `Community 34`, `Community 35`, `Community 2`, `Community 37`, `Community 6`, `Community 73`, `Community 10`, `Community 75`, `Community 44`, `Community 45`, `Community 14`, `Community 46`, `Community 47`, `Community 50`, `Community 24`, `Community 25`, `Community 27`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 24` to `Community 0`, `Community 66`, `Community 99`, `Community 3`, `Community 5`, `Community 6`, `Community 71`, `Community 75`, `Community 46`, `Community 47`, `Community 16`, `models.py`, `Community 53`, `Community 22`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `Job` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`Job` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 93 inferred relationships involving `main()` (e.g. with `.test_aggregate_local_flow_audit_failure_returns_nonzero_without_writing()` and `.test_aggregate_local_flow_writes_artifact_and_prints_summary()`) actually correct?**
  _`main()` has 93 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `version`, `private` to the rest of the system?**
  _538 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.10374149659863946 - nodes in this community are weakly interconnected._