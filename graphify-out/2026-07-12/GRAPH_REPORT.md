# Graph Report - aethermesh-core  (2026-07-12)

## Corpus Check
- 137 files · ~182,010 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2220 nodes · 5980 edges · 107 communities (92 shown, 15 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 399 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `656b78cf`
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
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]

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
- `CapabilityRecordTests` --uses--> `CapabilityRecordError`  [INFERRED]
  tests/test_capability_record.py → src/aethermesh_core/capability_record.py
- `QualityGateEdgeCoverageTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/flow_audit.py
- `IdentityPersistenceTests` --uses--> `HardwareIdentityInputs`  [INFERRED]
  tests/test_identity.py → src/aethermesh_core/identity.py
- `IdentityPersistenceTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_identity.py → src/aethermesh_core/identity.py
- `QualityGateEdgeCoverageTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/identity.py

## Import Cycles
- None detected.

## Communities (107 total, 15 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (8): NodeIdentity, Identity for one local node., build_text_stats_output(), LocalRunner, Build deterministic text statistics for a local ``text_stats`` job., Execute supported local job types for a node., Run one local job and return a structured result., LocalRunnerTests

### Community 1 - "Community 1"
Cohesion: 0.15
Nodes (16): announce_local_node(), build_node_announcement_message_log_document(), build_node_heartbeat_message(), NodeAnnouncementError, normalize_announcement_capabilities(), Local-only node heartbeat announcement helpers., Build and write one local node heartbeat announcement message log., Raised when a local node announcement cannot be built or written safely. (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (11): load_local_inbox(), local_inbox_path(), materialize_local_inboxes(), Load and validate only ``node_id``'s local transport inbox messages., Return the deterministic inbox path for ``node_id``., Materialize addressed messages from a message log into per-node inbox files., _emitted_message(), _failing_atomic_write_json() (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (12): Return capped integer contribution units for one validated local result.      Th, score_validated_contribution(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., _invalid(), Validate a reported result against the assigned local job.      The current prot (+4 more)

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
Cohesion: 0.07
Nodes (31): shouldLeaveBackgroundNodeRunning(), shouldStopTemporaryNode(), fs, getBundledRuntimePath(), getRuntimeExecutableName(), path, resolveRuntimeCommand(), getAetherMeshPaths() (+23 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (3): main(), main(), CliTests

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (32): _background_mode_enabled(), _control_background_node(), init(), jobs(), _local_api_is_aethermesh(), main(), node_start(), node_status() (+24 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (51): _bytes_to_gb(), collect_hardware_identity_inputs(), _colon_value(), _count_display_chips(), _csv_first_value(), _darwin_hardware_inputs(), _darwin_physical_mac_addresses(), _default_goos() (+43 more)

### Community 12 - "Community 12"
Cohesion: 0.14
Nodes (44): platformNotes(), apiClient, { app, BrowserWindow, ipcMain }, assertPortAvailableForAetherMesh(), { BackgroundNodeManager, UPDATE_INTERVAL_MS }, backgroundStateFromSettings(), bootstrap(), bootstrapState (+36 more)

### Community 13 - "Community 13"
Cohesion: 0.15
Nodes (31): CapabilityRecordError, Validation for the local-only version 1 capability record contract., Raised when a local capability record is incomplete or dishonest., _reject_unknown_fields(), _require_attribution(), _require_capability_version(), _require_identifier(), _require_identifier_list() (+23 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (65): _accepted_result(), aggregate_local_flow(), AggregationError, build_local_flow_aggregate(), _is_accepted(), Deterministic local aggregation for completed flow artifact directories., Raised when a local flow aggregate cannot be built or written safely., Build a deterministic aggregate document after auditing a flow directory. (+57 more)

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
Cohesion: 0.12
Nodes (30): configured_runtime_path(), configured_runtime_ref(), default_local_runtime_config(), load_local_runtime_config(), load_optional_local_runtime_config(), load_or_create_local_runtime_config(), LocalRuntimeConfig, LocalRuntimeConfigError (+22 more)

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
Cohesion: 0.17
Nodes (8): InboxReplayRequest, _coerce_node(), LocalScheduler, _normalize_capabilities(), Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., ScheduledNode, LocalSchedulerTests

### Community 23 - "Community 23"
Cohesion: 0.20
Nodes (17): build_parser(), format_duration(), format_progress_line(), main(), max_non_killed_for_score(), parse_mutmut_counts(), parse_mutmut_progress(), Return latest mutmut progress counters from text. (+9 more)

### Community 24 - "Community 24"
Cohesion: 0.11
Nodes (13): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), build_message_log_document(), Build a deterministic version 1 audit document for local mesh messages., LocalSimulationResult, Structured, deterministic output from a local multi-node simulation., Run local jobs across local node identities using scheduler assignment.      Thi, run_local_simulation() (+5 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (15): Load an existing message log and return a read-only peer roster., Run local file transport with workers discovered from heartbeat peers., run_peer_transport_flow(), summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError (+7 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (14): AetherMesh Core Persistent Goal, AI Direction, Build Direction, Contribution Tracking Direction, Current Priority Bias, Decision Rule For Every Interval, Development Philosophy, Early Prototype Target (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (17): _canonical_root_json(), _component_hashes(), deterministic_machine_node_id(), deterministic_machine_node_name(), HardwareComponentHashes, _index_from_hash(), _node_name_from_hashes(), print_hardware_node_id_debug() (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.24
Nodes (3): Validate and return one local-only capability record without writing it.      A, validate_capability_record(), CapabilityRecordTests

### Community 30 - "Community 30"
Cohesion: 0.18
Nodes (7): Assignment-only local dispatch for manifest-backed batches., Deterministic local node registry for simulation roster state., Read-only local peer roster derived from heartbeat messages., _coerce_job(), Deterministic local scheduler for the AetherMesh prototype., Minimal scheduler view of a job., ScheduledJob

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (13): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace., Raised when a local node-state JSON file cannot be safely loaded or saved., Durable local record of assignment messages already processed by one node. (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (28): _run_local_flow_with_roster(), ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally., build_receipt_document(), _json_compatible_dict(), _json_compatible_list(), _json_compatible_value(), load_receipt_document_if_exists() (+20 more)

### Community 33 - "Community 33"
Cohesion: 0.25
Nodes (8): CLI and Local UI Architecture, Commands, Desktop launcher, Install, Local API, Local dashboard, Security default, Shape

### Community 34 - "Community 34"
Cohesion: 0.47
Nodes (3): build_parser(), ArgumentParser, build_parser()

### Community 35 - "Community 35"
Cohesion: 0.09
Nodes (29): _create_identity_document_without_overwrite(), Create an identity JSON file atomically without replacing a winner., atomic_create_json(), _publish_json(), Create one JSON document atomically without replacing an existing file., _configured_path(), _contains_runtime_artifacts(), _default_manifest_document() (+21 more)

### Community 36 - "Community 36"
Cohesion: 0.60
Nodes (4): isDestroyedElectronObject(), isDestroyedError(), sendWindowState(), appendBootstrapLog()

### Community 37 - "Community 37"
Cohesion: 0.10
Nodes (10): _identity_document(), load_or_create_identity(), parse_local_node_identity_document(), Parse and validate the Phase 1 public local node identity shape., Load a versioned local node identity, creating one if the file is missing., _run_command(), _save_identity(), HostnameReader (+2 more)

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
Cohesion: 0.10
Nodes (13): LocalMessageBus, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., Create and send a message with the next deterministic bus sequence id., send_numbered_message() (+5 more)

### Community 44 - "Community 44"
Cohesion: 0.10
Nodes (28): _run_json_command(), canonical_json_hash(), Hash a JSON object in stable key order for local receipts., _append_log(), _artifact_refs(), _document_hash(), _interrupted_work_refs(), _iter_files() (+20 more)

### Community 45 - "Community 45"
Cohesion: 0.10
Nodes (33): LocalStartupResult, Serializable summary for one accepted local node startup., Return a JSON-serializable startup summary with local-only refs., _artifact_refs(), _attribution_id(), _error_summary(), inspect_local_node_runtime(), _lineage_parent() (+25 more)

### Community 46 - "Community 46"
Cohesion: 0.20
Nodes (21): collect_local_outboxes(), _load_inbox_document(), _load_outbox_document(), local_outbox_path(), LocalTransportError, _message_from_outbox_entry(), _messages_from_outbox_document(), _node_id_from_transport_filename() (+13 more)

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (18): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), _load_manifest_document(), load_manifest_jobs(), LocalJobBatch, ManifestError, _parse_capabilities() (+10 more)

### Community 48 - "models.py"
Cohesion: 0.17
Nodes (11): AetherMesh Core local prototype package., Contribution ledger helpers for local job results., MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Core data models for the local AetherMesh prototype., Local-only node inbox processing service for assigned work messages., Canonical SHA-256 hashing for accounted local job results. (+3 more)

### Community 49 - "Community 49"
Cohesion: 0.23
Nodes (16): build_update_plan(), _checksum_for_asset(), _fetch_bytes(), _fetch_json(), _find_asset(), _install_wheel(), _optional_string_field(), Install the newest AetherMesh package from the latest GitHub release. (+8 more)

### Community 51 - "Community 51"
Cohesion: 0.25
Nodes (7): Capability-version changes, Conditional validation fields, Local Capability Record Schema, Optional lineage fields, Required fields, Valid passed record, Valid unvalidated record

### Community 52 - "Community 52"
Cohesion: 0.10
Nodes (19): author, description, devDependencies, electron, electron-builder, main, name, private (+11 more)

### Community 53 - "Community 53"
Cohesion: 0.12
Nodes (10): NodeRuntimeService, Run a queued local submission; this is not a daemon or remote boundary., Central service for local node config, lifecycle status, peers, and jobs., Return read-only, redacted summaries of locally registered experts., Return local job buckets without faking work., Read one submission and its optional local execution evidence., Read derived local job audit events without mutating stored evidence., Read local job evidence into a deterministic, non-mutating summary. (+2 more)

### Community 54 - "Community 54"
Cohesion: 0.15
Nodes (22): _contains_secret_identity_fragment(), _identity_artifact_has_identity_metadata(), _identity_artifact_mentions_node(), _identity_document_creator_node_id(), IdentityPersistenceError, _load_identity(), _load_identity_document(), _load_local_identity_ref_document_if_exists() (+14 more)

### Community 55 - "Community 55"
Cohesion: 0.18
Nodes (7): ModuleType, RuntimeError, DesktopReleaseWorkflowTests, load_quality_gates_module(), WorkflowSecurityTests, FullTestRunnerTests, load_full_test_module()

### Community 56 - "Community 56"
Cohesion: 0.06
Nodes (35): _mark_ephemeral_artifact(), Load an existing ledger and return read-only aggregate totals., run_demo(), summarize_ledger(), _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary (+27 more)

### Community 57 - "Community 57"
Cohesion: 0.13
Nodes (15): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), _mark_ephemeral_message_log(), _node_ids_from_replayed_messages(), process_local_inbox(), Replay a saved local message log or local transport inbox for one node., Replay saved local messages and return payload plus structured result., _fallback_job_id() (+7 more)

### Community 58 - "release_update.py"
Cohesion: 0.10
Nodes (25): _config_api_host(), _config_api_port(), _config_enabled_work_types(), _config_identity_path(), _config_identity_persistence_enabled(), _config_node_id(), _config_node_name(), _default_home() (+17 more)

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

### Community 67 - "Desktop Troubleshooting"
Cohesion: 0.17
Nodes (11): AetherMesh CLI, CLI shim paths, Linux, macOS, Manual tests, PATH setup, Repair CLI, Runtime updates (+3 more)

### Community 68 - "Community 68"
Cohesion: 0.12
Nodes (5): create_app(), Create the localhost API/dashboard app used by CLI and UI frontends., ApiErrorTests, ModelManifestInspectionTests, RuntimeServiceTests

### Community 69 - "Community 69"
Cohesion: 0.18
Nodes (10): API did not start, Bundled runtime missing, Desktop Troubleshooting, Development fallback, Linux `.deb` package metadata, Linux system dependency missing, macOS Gatekeeper, Node already running (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.18
Nodes (10): args, built, entry, fs, nodeNameWordlists, path, result, root (+2 more)

### Community 73 - "Community 73"
Cohesion: 0.14
Nodes (10): _ephemeral_roster(), _log_ephemeral_identity_active(), _node_artifact_filename(), _node_artifact_path(), Command-line interface for the local AetherMesh prototype., Return a deterministic, non-merging filename for one manifest node id., _require_int_result_field(), _use_ephemeral_identity() (+2 more)

### Community 74 - "REVA Pipeline"
Cohesion: 0.25
Nodes (8): AEF — Aether Expert Fabric, AER — Adaptive Expert Routing, Aggregator, Core Terms, Expert, REVA Pipeline, Router, Validator

### Community 75 - "Community 75"
Cohesion: 0.17
Nodes (9): dispatch_peer_batch_command(), Dispatch manifest jobs to heartbeat-derived peers without execution., dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., Build a local dispatch log with heartbeats and job assignments only.      This f (+1 more)

### Community 76 - "Community 76"
Cohesion: 0.20
Nodes (8): Shared JSON file persistence helpers for local-only artifacts., Best-effort removal for abandoned atomic-write temp files., remove_temp_file(), JSON-backed local message log persistence for batch simulations., Local mesh message envelopes for deterministic simulation output., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible()

### Community 77 - "Community 77"
Cohesion: 0.39
Nodes (7): detectPython(), { execFile }, execFileAsync, isUsablePythonVersion(), parsePythonVersion(), { promisify }, runVersion()

### Community 78 - "Community 78"
Cohesion: 0.29
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
Cohesion: 0.33
Nodes (6): Canonical states, Local Node Lifecycle, Persisted fields for lifecycle-changing events, Restart recovery, Scope boundaries, Transition events and validation conditions

### Community 85 - "Community 85"
Cohesion: 0.47
Nodes (5): buildPackageInstallCommand(), DEFAULT_SETTINGS, normalizePackageSettings(), defaultSettings(), normalizeSettings()

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (5): fs, path, root, target, targetDir

### Community 87 - "Community 87"
Cohesion: 0.17
Nodes (11): additionalProperties, $id, minLength, type, properties, message, required, $schema (+3 more)

### Community 88 - "Community 88"
Cohesion: 0.40
Nodes (4): main, name, private, version

### Community 89 - "Community 89"
Cohesion: 0.12
Nodes (13): _message_from_inbox_entry(), build_collected_outbox_message_log_document(), build_flow_message_log_document(), _message_from_document_entry(), _message_to_document_entry(), Build a deterministic version 1 run-level local flow message log., Build a deterministic version 1 log from collected local transport outboxes., MeshMessage (+5 more)

### Community 92 - "Community 92"
Cohesion: 0.09
Nodes (16): _append_identity_reset_receipt(), _backup_identity_referenced_artifacts(), _identity_reset_artifact_ref(), _identity_reset_warning(), IdentityResetResult, _load_identity_reset_receipts(), _local_identity_ref_path(), Return a local audit reference without leaking host-specific directories. (+8 more)

### Community 94 - "Community 94"
Cohesion: 0.50
Nodes (4): build_text_chunk_output(), _preferred_text_chunk_split(), Build stable character chunks for a local ``text_chunk`` job., Return a deterministic split point no later than ``hard_end``.

### Community 96 - "Community 96"
Cohesion: 0.29
Nodes (4): _canonical_json_bytes(), Hash the canonical result fields used by result messages and audits., result_hash_from_fields(), ResultHashTests

### Community 98 - "Community 98"
Cohesion: 0.14
Nodes (13): capture_version_metadata(), _node_software_version(), Locally observable software and runtime version metadata., Raised when local version metadata is missing or malformed., Return factual local software/runtime metadata for one node run., Validate and return a shallow copy of a version metadata document., _require_non_empty_string(), _require_utc_timestamp() (+5 more)

### Community 99 - "Community 99"
Cohesion: 0.40
Nodes (4): Allow readable local identifiers while rejecting path and URI-shaped values., Accept one local job request without dispatching or validating it., _safe_local_artifact_ref(), _safe_local_identifier()

### Community 101 - "Community 101"
Cohesion: 0.13
Nodes (13): _error_response(), _lifespan(), Local FastAPI app for the AetherMesh node dashboard., Return the stable, deliberately non-provenance API error envelope., Classify expected local runtime failures without exposing their text., _request_id(), _runtime_error_code(), FastAPI (+5 more)

### Community 103 - "Community 103"
Cohesion: 0.40
Nodes (4): NoAvailableNodesError, Raised when local job assignment has jobs but no available nodes., Assign jobs to available capable nodes with deterministic fair ordering., ValueError

### Community 104 - "Community 104"
Cohesion: 0.33
Nodes (3): atomic_write_json(), Write one JSON document using a temp file and atomic replace., JsonIoTests

### Community 105 - "Community 105"
Cohesion: 0.40
Nodes (4): _classify_startup_error(), Keep startup errors shareable by removing absolute host paths., Attach stable automation fields without including local configuration values., _redact_local_paths()

### Community 106 - "Community 106"
Cohesion: 0.50
Nodes (3): LocalNodeIdentity, Validated version 1 public local node identity document., Return the public identity document without private key material.

## Knowledge Gaps
- **258 isolated node(s):** `name`, `version`, `private`, `main`, `{ spawnSync }` (+253 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MeshMessage` connect `Community 89` to `Community 32`, `Community 1`, `Community 2`, `Community 5`, `Community 6`, `Community 8`, `Community 75`, `Community 43`, `Community 76`, `Community 14`, `Community 46`, `models.py`, `Community 16`, `Community 22`, `Community 24`, `Community 57`, `Community 25`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `NodeIdentity` connect `Community 0` to `Community 3`, `Community 11`, `Community 22`, `Community 24`, `Community 27`, `Community 32`, `Community 37`, `Community 43`, `models.py`, `Community 53`, `Community 54`, `Community 56`, `Community 57`, `release_update.py`, `Community 71`, `Community 73`, `Community 92`, `Community 98`, `Community 106`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 32`, `Community 0`, `release_update.py`, `Community 5`, `Community 6`, `Community 71`, `Community 75`, `Community 47`, `Community 16`, `models.py`, `Community 53`, `Community 22`, `Community 24`, `Community 57`, `Community 56`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `Job` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`Job` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 93 inferred relationships involving `main()` (e.g. with `.test_aggregate_local_flow_audit_failure_returns_nonzero_without_writing()` and `.test_aggregate_local_flow_writes_artifact_and_prints_summary()`) actually correct?**
  _`main()` has 93 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `version`, `private` to the rest of the system?**
  _548 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.13229018492176386 - nodes in this community are weakly interconnected._