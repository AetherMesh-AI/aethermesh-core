# Graph Report - aethermesh-core  (2026-07-10)

## Corpus Check
- 126 files · ~166,332 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2023 nodes · 5276 edges · 95 communities (81 shown, 14 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 292 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `89c5eb30`
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
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
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
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]

## God Nodes (most connected - your core abstractions)
1. `Job` - 150 edges
2. `main()` - 121 edges
3. `MeshMessage` - 97 edges
4. `JobResult` - 89 edges
5. `NodeIdentity` - 78 edges
6. `IdentityPersistenceTests` - 73 edges
7. `CliTests` - 72 edges
8. `ScheduledNode` - 53 edges
9. `start_local_node()` - 51 edges
10. `validate_job_result()` - 51 edges

## Surprising Connections (you probably didn't know these)
- `LocalFlowAggregationTests` --uses--> `AggregationError`  [INFERRED]
  tests/test_aggregation.py → src/aethermesh_core/aggregation.py
- `LocalFlowAggregationTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_aggregation.py → src/aethermesh_core/flow_audit.py
- `QualityGateEdgeCoverageTests` --uses--> `FlowAuditError`  [INFERRED]
  tests/test_quality_gate_edges.py → src/aethermesh_core/flow_audit.py
- `IdentityPersistenceTests` --uses--> `HardwareIdentityInputs`  [INFERRED]
  tests/test_identity.py → src/aethermesh_core/identity.py
- `IdentityPersistenceTests` --uses--> `IdentityPersistenceError`  [INFERRED]
  tests/test_identity.py → src/aethermesh_core/identity.py

## Import Cycles
- None detected.

## Communities (95 total, 14 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (5): NodeIdentity, Identity for one local node., LocalRunner, Execute supported local job types for a node., LocalRunnerTests

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (16): announce_local_node(), build_node_announcement_message_log_document(), build_node_heartbeat_message(), NodeAnnouncementError, normalize_announcement_capabilities(), Local-only node heartbeat announcement helpers., Build and write one local node heartbeat announcement message log., Raised when a local node announcement cannot be built or written safely. (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.14
Nodes (12): _mark_ephemeral_artifact(), run_demo(), ContributionLedger, load_existing_ledger_document(), load_ledger_document(), Small in-memory ledger for prototype contribution accounting., Serialize the ledger into the small local JSON file shape., Load a JSON-backed local ledger, treating a missing file as empty.      The retu (+4 more)

### Community 3 - "Community 3"
Cohesion: 0.16
Nodes (11): Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., _invalid(), Local validation gate for reported AetherMesh job results., Deterministic outcome from validating one reported job result., Validate a reported result against the assigned local job.      The current prot (+3 more)

### Community 4 - "Community 4"
Cohesion: 0.20
Nodes (10): AetherMesh Core, Current status, Development principles, Documentation, Install for development, License, Prototype flow examples, Quick start (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (20): _assignment_key(), _job_from_assignment(), LocalValidationError, Independent local replay validation for reported AetherMesh job results., Normalize credited local result messages back to runner-result shape.      Worke, Raised when local validation replay cannot safely produce an artifact., Replay assignment/result logs and write an independent validation report., _required_non_empty_string() (+12 more)

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (8): AetherMesh Core local prototype package., _accounted_units(), Contribution ledger helpers for local job results., Record one result and return its local contribution record.          Only comple, _remove_temp_file(), _string_output(), Core data models for the local AetherMesh prototype., Local-only node inbox processing service for assigned work messages.

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (13): LocalMessageBus, MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log. (+5 more)

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (49): _background_mode_enabled(), _control_background_node(), init(), jobs(), _local_api_is_aethermesh(), main(), node_start(), node_status() (+41 more)

### Community 11 - "Community 11"
Cohesion: 0.11
Nodes (47): _bytes_to_gb(), collect_hardware_identity_inputs(), _colon_value(), _count_display_chips(), _csv_first_value(), _darwin_hardware_inputs(), _darwin_physical_mac_addresses(), _extract_labeled_value() (+39 more)

### Community 12 - "Community 12"
Cohesion: 0.16
Nodes (13): load_local_inbox(), local_inbox_path(), materialize_local_inboxes(), Load and validate only ``node_id``'s local transport inbox messages., Return the deterministic inbox path for ``node_id``., Raised when a file-backed local transport artifact cannot be loaded or saved., Materialize addressed messages from a message log into per-node inbox files., Write one version 1 local transport inbox with an atomic replace. (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.05
Nodes (36): Run a local simulation from a validated JSON manifest., Load an existing message log and return a read-only peer roster., run_local_batch(), summarize_peers(), load_job_manifest(), _load_manifest_document(), load_manifest_jobs(), LocalJobBatch (+28 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (13): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Versioned local node processing state persistence., Write a local node-state JSON document via temp-file then atomic replace., Raised when a local node-state JSON file cannot be safely loaded or saved., Durable local record of assignment messages already processed by one node. (+5 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (44): platformNotes(), apiClient, { app, BrowserWindow, ipcMain }, assertPortAvailableForAetherMesh(), { BackgroundNodeManager, UPDATE_INTERVAL_MS }, backgroundStateFromSettings(), bootstrap(), bootstrapState (+36 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (23): build_collected_outbox_message_log_document(), build_flow_message_log_document(), build_message_log_document(), build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages(), load_worker_emitted_messages(), _message_from_document_entry() (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.24
Nodes (16): CompletedProcess, Namespace, changed_pyproject_from_base(), command_artifact_provenance(), command_dependency_audit(), command_dependency_review(), command_mutation_score(), command_pr_size() (+8 more)

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (36): _assert_assignment_matches_receipt(), _assert_contribution_message_matches_receipt(), _assert_equal(), _assert_message_order(), _assert_result_message_matches_receipt(), _assert_validation_message_matches_receipt(), audit_local_flow(), _find_flow_message_for_receipt() (+28 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (11): NodeRegistry, Deterministic local node registry for simulation roster state., In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order. (+3 more)

### Community 20 - "Community 20"
Cohesion: 0.14
Nodes (18): _config_api_host(), _config_api_port(), _config_identity_path(), _config_identity_persistence_enabled(), _config_node_id(), _config_node_name(), _default_home(), _memory_total_bytes() (+10 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (9): _message_from_inbox_entry(), message_from_mapping(), Local mesh message envelopes for deterministic simulation output., Build a validated MeshMessage from a JSON-like mapping., _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible(), MeshMessageTests (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.21
Nodes (6): _coerce_node(), LocalScheduler, Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., ScheduledNode, LocalSchedulerTests

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (24): ModuleType, RuntimeError, build_parser(), format_duration(), format_progress_line(), main(), max_non_killed_for_score(), parse_mutmut_counts() (+16 more)

### Community 24 - "Community 24"
Cohesion: 0.14
Nodes (10): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), LocalSimulationResult, Local multi-node simulation for the AetherMesh prototype., Structured, deterministic output from a local multi-node simulation., Run local jobs across local node identities using scheduler assignment.      Thi, run_local_simulation(), _summary_to_simulation_dict() (+2 more)

### Community 25 - "Community 25"
Cohesion: 0.30
Nodes (14): _base_checks(), build_parser(), Check, _checks_for_mode(), _command_available(), _full_extra_checks(), main(), _merged_env() (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.05
Nodes (39): AEF: Aether Expert Fabric, AER: Adaptive Expert Routing, AetherMesh Core Architecture, Aggregator, Contribution tracking direction, Core responsibilities, Current prototype layer, Decision rule for new work (+31 more)

### Community 27 - "Community 27"
Cohesion: 0.10
Nodes (22): _canonical_root_json(), _component_hashes(), _default_goos(), deterministic_machine_node_id(), deterministic_machine_node_name(), HardwareComponentHashes, HardwareIdentityInputs, _index_from_hash() (+14 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (16): dispatch_peer_batch_command(), Dispatch manifest jobs to heartbeat-derived peers without execution., build_dispatch_message_log_document(), Build a deterministic version 1 assignment-only dispatch document., _coerce_job(), JobAssignment, NoAvailableNodesError, _normalize_capabilities() (+8 more)

### Community 29 - "Community 29"
Cohesion: 0.17
Nodes (8): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Assignment-only local dispatch for manifest-backed batches., Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., Build a local dispatch log with heartbeats and job assignments only.      This f, DispatchTests

### Community 30 - "Community 30"
Cohesion: 0.22
Nodes (10): atomic_create_json(), atomic_write_json(), _publish_json(), Shared JSON file persistence helpers for local-only artifacts., Write one JSON document using a temp file and atomic replace., Create one JSON document atomically without replacing an existing file., Best-effort removal for abandoned atomic-write temp files., remove_temp_file() (+2 more)

### Community 31 - "Community 31"
Cohesion: 0.07
Nodes (33): shouldLeaveBackgroundNodeRunning(), shouldStopTemporaryNode(), detectPython(), { execFile }, execFileAsync, isUsablePythonVersion(), parsePythonVersion(), { promisify } (+25 more)

### Community 32 - "Community 32"
Cohesion: 0.12
Nodes (25): ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally., build_receipt_document(), _json_compatible_dict(), _json_compatible_list(), _json_compatible_value(), load_receipt_document_if_exists(), _output_summary() (+17 more)

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (8): CLI and Local UI Architecture, Commands, Desktop launcher, Install, Local API, Local dashboard, Security default, Shape

### Community 35 - "Community 35"
Cohesion: 0.14
Nodes (21): _configured_path(), _default_manifest_document(), _document_hash(), _ensure_manifest_directories(), _ensure_runtime_dirs(), _identity_creator_node_id(), _load_json_object(), _load_manifest() (+13 more)

### Community 36 - "Community 36"
Cohesion: 0.10
Nodes (15): BackgroundNodeManager, buildLaunchAgentPlist(), buildSystemdUserService(), buildWindowsTaskXml(), crypto, { execFile: defaultExecFile }, execFilePromise(), fs (+7 more)

### Community 37 - "Community 37"
Cohesion: 0.10
Nodes (11): _identity_document(), load_or_create_identity(), _new_local_node_id(), _node_name_wordlist_dir(), Load a versioned local node identity, creating one if the file is missing., Return a legacy collision-resistant local node id for explicit rotations., _run_command(), _save_identity() (+3 more)

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (25): allowed_next_states(), canonical_lifecycle_states(), LifecycleRecord, LifecycleStateSpec, LifecycleTransitionError, LocalNodeLifecycleState, Local-first lifecycle model for one AetherMesh node runtime., Canonical local node lifecycle states. (+17 more)

### Community 41 - "Community 41"
Cohesion: 0.10
Nodes (25): _contains_secret_identity_fragment(), _create_identity_document_without_overwrite(), _identity_artifact_has_identity_metadata(), _identity_artifact_mentions_node(), _identity_document_creator_node_id(), IdentityPersistenceError, _load_identity(), _load_identity_document() (+17 more)

### Community 42 - "Community 42"
Cohesion: 0.11
Nodes (25): load_json_mapping(), Small JSON helpers shared by local lifecycle commands., Read a required JSON object and raise the caller's local error type., Return a non-empty string field or raise the caller's local error type., require_text_field(), _append_log(), _document_hash(), _load_json_object() (+17 more)

### Community 43 - "Community 43"
Cohesion: 0.12
Nodes (19): buildPosixShim(), buildShellPathBlock(), buildWindowsCmdShim(), buildWindowsPowerShellShim(), CliManager, { execFile: defaultExecFile }, execFilePromise(), fs (+11 more)

### Community 44 - "Community 44"
Cohesion: 0.11
Nodes (24): append_json_line(), canonical_json_hash(), Append one deterministic JSONL entry to a local lifecycle log., Hash a JSON object in stable key order for local receipts., _append_log(), _artifact_refs(), _document_hash(), _interrupted_work_refs() (+16 more)

### Community 45 - "Community 45"
Cohesion: 0.11
Nodes (23): LocalStartupResult, Serializable summary for one accepted local node startup., Return a JSON-serializable startup summary with local-only refs., _artifact_refs(), inspect_local_node_runtime(), _load_runtime_json(), LocalRuntimeInspectError, Explicit local node runtime API shared by CLI and tests.  This module is the bou (+15 more)

### Community 46 - "Community 46"
Cohesion: 0.12
Nodes (29): dispatch_local_batch_command(), _emitted_messages_from_inbox_result(), _ephemeral_roster(), _inbox_process_result_to_dict(), InboxReplayRequest, _log_ephemeral_identity_active(), _mark_ephemeral_message_log(), _node_artifact_filename() (+21 more)

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (25): configured_runtime_path(), configured_runtime_ref(), default_local_runtime_config(), load_local_runtime_config(), load_optional_local_runtime_config(), load_or_create_local_runtime_config(), LocalRuntimeConfig, LocalRuntimeConfigError (+17 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (15): capture_version_metadata(), _node_software_version(), Locally observable software and runtime version metadata., Return a stable local reference for one validated metadata document., Raised when local version metadata is missing or malformed., Return factual local software/runtime metadata for one node run., Validate and return a shallow copy of a version metadata document., _require_non_empty_string() (+7 more)

### Community 49 - "Community 49"
Cohesion: 0.18
Nodes (19): collect_local_outboxes(), _load_inbox_document(), _load_outbox_document(), local_outbox_path(), LocalTransportError, _message_from_outbox_entry(), _messages_from_outbox_document(), _node_id_from_transport_filename() (+11 more)

### Community 51 - "Community 51"
Cohesion: 0.11
Nodes (12): _append_identity_reset_receipt(), _identity_reset_artifact_ref(), _identity_reset_warning(), IdentityResetResult, _load_identity_reset_receipts(), Return a local audit reference without leaking host-specific directories., Local audit details for an explicit identity reset., Return JSON-serializable reset details for CLI/API callers. (+4 more)

### Community 52 - "Community 52"
Cohesion: 0.10
Nodes (19): author, description, devDependencies, electron, electron-builder, main, name, private (+11 more)

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (19): AER — Adaptive Expert Routing, AetherMesh Core, AetherMesh Core Persistent Goal, ai/local-loop-20260702-072353-1, Architecture direction, Core Terms, Development approach, docs/persistent-goal.md excerpt (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.10
Nodes (19): AER — Adaptive Expert Routing, AetherMesh Core, AetherMesh Core Persistent Goal, ai/local-loop-20260702-072353-1, Architecture direction, Core Terms, Development approach, docs/persistent-goal.md excerpt (+11 more)

### Community 55 - "Community 55"
Cohesion: 0.20
Nodes (14): _accepted_result(), AggregationError, build_local_flow_aggregate(), _is_accepted(), Deterministic local aggregation for completed flow artifact directories., Raised when a local flow aggregate cannot be built or written safely., Build a deterministic aggregate document after auditing a flow directory., Write an aggregate document via temp-file then atomic replace. (+6 more)

### Community 56 - "Community 56"
Cohesion: 0.16
Nodes (10): ContributionRecord, LedgerPersistenceError, Audit record derived from one local job result., Deserialize a ledger from the local JSON file shape., Raised when a local ledger JSON file cannot be safely loaded or saved., Serialize the record into a JSON-compatible dictionary., Deserialize one JSON-compatible contribution record., _record_from_json_value() (+2 more)

### Community 57 - "Community 57"
Cohesion: 0.18
Nodes (7): NodeRuntimeService, Create local runtime directories, identity, config, and log seed data., Prepare local runtime state before a foreground API/node process starts., Return local prototype capabilities exposed to desktop/API frontends., Return local job buckets without faking work., Central service for local node config, lifecycle status, peers, and jobs., Load local node config, returning a default view when missing.

### Community 58 - "Community 58"
Cohesion: 0.25
Nodes (17): ArgumentParser, build_parser(), build_release_metadata(), command_prepare(), Commit, commits_since(), format_release_notes(), head_sha() (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.24
Nodes (13): _cap_units(), _ceil_div(), _non_negative_int(), Deterministic contribution scoring for validated local workload results., _score_keyword_extract(), _score_text_chunk(), _score_text_embed(), _score_text_retrieve() (+5 more)

### Community 60 - "Community 60"
Cohesion: 0.15
Nodes (14): build_keyword_extract_output(), build_text_chunk_output(), build_text_embed_output(), build_text_retrieve_output(), build_text_stats_output(), _preferred_text_chunk_split(), Local in-memory runner for the first AetherMesh executable slice., Build deterministic text statistics for a local ``text_stats`` job. (+6 more)

### Community 61 - "Community 61"
Cohesion: 0.19
Nodes (7): _canonical_json_bytes(), Canonical SHA-256 hashing for accounted local job results., Return the canonical lowercase SHA-256 digest for a ``JobResult``.      The hash, Hash the canonical result fields used by result messages and audits., result_hash(), result_hash_from_fields(), ResultHashTests

### Community 62 - "Community 62"
Cohesion: 0.34
Nodes (3): _assignment(), LocalNodeServiceTests, _service()

### Community 64 - "Community 64"
Cohesion: 0.29
Nodes (11): bootstrapState, els, formatBool(), refreshDashboard(), renderBackground(), renderCapabilities(), renderCli(), renderPeers() (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.33
Nodes (6): aggregate_local_flow(), Audit, build, and persist a local flow aggregate, returning a CLI summary., _load_json(), LocalFlowAggregationTests, _write_json(), _write_manifest()

### Community 66 - "Community 66"
Cohesion: 0.32
Nodes (4): Return capped integer contribution units for one validated local result.      Th, score_validated_contribution(), ContributionScoringTests, _run()

### Community 67 - "Community 67"
Cohesion: 0.24
Nodes (6): _fallback_job_id(), _job_from_assignment_payload(), LocalNodeService, Synchronous local-only handler for one node's assigned-work inbox., Process unhandled ``job_assigned`` messages addressed to this node.          The, QualityGateEdgeCoverageTests

### Community 68 - "Community 68"
Cohesion: 0.24
Nodes (3): Filesystem paths used by one local AetherMesh runtime., RuntimePaths, RuntimeServiceTests

### Community 69 - "Community 69"
Cohesion: 0.17
Nodes (11): AetherMesh CLI, CLI shim paths, Linux, macOS, Manual tests, PATH setup, Repair CLI, Runtime updates (+3 more)

### Community 70 - "Community 70"
Cohesion: 0.29
Nodes (7): create_app(), _lifespan(), Local FastAPI app for the AetherMesh node dashboard., Create the localhost API/dashboard app used by CLI and UI frontends., FastAPI, ApiTests, _fetch_api_payloads()

### Community 71 - "Community 71"
Cohesion: 0.18
Nodes (11): AetherMesh CLI, AetherMesh Desktop, Deferred work, Development commands, Manual validation, Packaging targets, Runtime model, Runtime update behavior (+3 more)

### Community 72 - "Community 72"
Cohesion: 0.18
Nodes (10): API did not start, Bundled runtime missing, Desktop Troubleshooting, Development fallback, Linux `.deb` package metadata, Linux system dependency missing, macOS Gatekeeper, Node already running (+2 more)

### Community 73 - "Community 73"
Cohesion: 0.18
Nodes (10): args, built, entry, fs, nodeNameWordlists, path, result, root (+2 more)

### Community 74 - "Community 74"
Cohesion: 0.20
Nodes (6): ContributionSummary, Serialize the summary into a JSON-compatible dictionary., Return deterministic aggregate totals for one local node., Return node ids present in the ledger in deterministic order., Return a deterministic JSON-compatible summary of all records., Aggregated contribution totals for one local node.

### Community 76 - "Community 76"
Cohesion: 0.32
Nodes (5): _backup_identity_referenced_artifacts(), _load_local_identity_ref_document_if_exists(), _local_identity_ref_path(), _string_list_from_section(), _unique_reset_artifact_path()

### Community 77 - "Community 77"
Cohesion: 0.29
Nodes (6): Background Node Manual Test Plan, Linux systemd user service, macOS LaunchAgent, Runtime update checks, Shared checks, Windows Task Scheduler

### Community 78 - "Community 78"
Cohesion: 0.29
Nodes (7): Local Node Identity Format, Local prototype reset procedure, Manifest linkage, Minimal example, Private key material, Version 1 document shape, Versioning rules

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (6): AetherMesh alignment, Follow-ups, Objective, Safety notes, Validation, What changed

### Community 82 - "Community 82"
Cohesion: 0.47
Nodes (5): buildPackageInstallCommand(), DEFAULT_SETTINGS, normalizePackageSettings(), defaultSettings(), normalizeSettings()

### Community 83 - "Community 83"
Cohesion: 0.53
Nodes (5): fs, getBundledRuntimePath(), getRuntimeExecutableName(), path, resolveRuntimeCommand()

### Community 84 - "Community 84"
Cohesion: 0.33
Nodes (6): Canonical states, Local Node Lifecycle, Persisted fields for lifecycle-changing events, Restart recovery, Scope boundaries, Transition events and validation conditions

### Community 85 - "Community 85"
Cohesion: 0.33
Nodes (5): fs, path, root, target, targetDir

### Community 87 - "Community 87"
Cohesion: 0.60
Nodes (4): isDestroyedElectronObject(), isDestroyedError(), sendWindowState(), appendBootstrapLog()

### Community 88 - "Community 88"
Cohesion: 0.40
Nodes (4): main, name, private, version

### Community 89 - "Community 89"
Cohesion: 0.50
Nodes (3): LocalNodeIdentity, Validated version 1 public local node identity document., Return the public identity document without private key material.

### Community 91 - "Community 91"
Cohesion: 0.67
Nodes (3): Background OS-managed mode, Temporary app-managed mode, Two node modes

## Knowledge Gaps
- **226 isolated node(s):** `name`, `version`, `private`, `main`, `{ spawnSync }` (+221 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 8` to `Community 1`, `Community 2`, `Community 5`, `Community 10`, `Community 12`, `Community 13`, `Community 18`, `Community 24`, `Community 28`, `Community 34`, `Community 35`, `Community 38`, `Community 44`, `Community 45`, `Community 46`, `Community 49`, `Community 50`, `Community 51`, `Community 65`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 32`, `Community 0`, `Community 2`, `Community 66`, `Community 67`, `Community 5`, `Community 6`, `Community 13`, `Community 46`, `Community 60`, `Community 16`, `Community 22`, `Community 24`, `Community 28`, `Community 29`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `NodeIdentity` connect `Community 0` to `Community 32`, `Community 2`, `Community 67`, `Community 68`, `Community 37`, `Community 6`, `Community 66`, `Community 41`, `Community 46`, `Community 48`, `Community 51`, `Community 20`, `Community 86`, `Community 24`, `Community 89`, `Community 27`, `Community 62`, `Community 57`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Path` (e.g. with `.test_run_demo_malformed_ledger_path_returns_cli_error()` and `.test_run_demo_persists_json_ledger_and_accumulates_summary()`) actually correct?**
  _`Path` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 21 inferred relationships involving `Job` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`Job` has 21 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `MeshMessage` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`MeshMessage` has 27 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `version`, `private` to the rest of the system?**
  _491 weakly-connected nodes found - possible documentation gaps or missing edges._