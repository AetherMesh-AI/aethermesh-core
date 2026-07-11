# Graph Report - aethermesh-core  (2026-07-11)

## Corpus Check
- 127 files · ~171,889 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2178 nodes · 5734 edges · 94 communities (81 shown, 13 thin omitted)
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 1613 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `03060658`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- models.py
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- release_update.py
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Desktop Troubleshooting
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- REVA Pipeline
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92

## God Nodes (most connected - your core abstractions)
1. `Job` - 150 edges
2. `main()` - 97 edges
3. `MeshMessage` - 97 edges
4. `JobResult` - 89 edges
5. `NodeIdentity` - 78 edges
6. `IdentityPersistenceTests` - 73 edges
7. `CliTests` - 72 edges
8. `start_local_node()` - 67 edges
9. `IdentityPersistenceError` - 64 edges
10. `ScheduledNode` - 51 edges

## Surprising Connections (you probably didn't know these)
- `_processed_assignment()` --calls--> `score_validated_contribution()`  [INFERRED]
  tests/test_receipts.py → src/aethermesh_core/contribution.py
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

## Communities (94 total, 13 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.16
Nodes (5): NodeIdentity, Identity for one local node., LocalRunner, Execute supported local job types for a node., LocalRunnerTests

### Community 1 - "Community 1"
Cohesion: 0.11
Nodes (19): announce_local_node(), build_node_announcement_message_log_document(), build_node_heartbeat_message(), NodeAnnouncementError, normalize_announcement_capabilities(), Any, Path, ValueError (+11 more)

### Community 2 - "Community 2"
Cohesion: 0.10
Nodes (14): LocalMessageBus, Any, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., Create and send a message with the next deterministic bus sequence id. (+6 more)

### Community 3 - "Community 3"
Cohesion: 0.18
Nodes (8): Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., _invalid(), Validate a reported result against the assigned local job.      The current prot, validate_job_result(), ValidationTests

### Community 4 - "Community 4"
Cohesion: 0.20
Nodes (10): AetherMesh Core, Current status, Development principles, Documentation, Install for development, License, Prototype flow examples, Quick start (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.17
Nodes (23): AssignmentKey, _assignment_key(), _job_from_assignment(), LocalValidationError, Any, Path, ValueError, Independent local replay validation for reported AetherMesh job results. (+15 more)

### Community 6 - "Community 6"
Cohesion: 0.33
Nodes (3): _ephemeral_roster(), Create a caller-usable ephemeral identity for local demo runs., NodeIdentityTests

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (15): BackgroundNodeManager, buildLaunchAgentPlist(), buildSystemdUserService(), buildWindowsTaskXml(), crypto, { execFile: defaultExecFile }, execFilePromise(), fs (+7 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (4): ValueError, Raised when local runtime state cannot be safely loaded or written., RuntimeServiceError, AppCliTests

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (57): CommandRunner, FileReader, _bytes_to_gb(), collect_hardware_identity_inputs(), _colon_value(), _contains_secret_identity_fragment(), _count_display_chips(), _csv_first_value() (+49 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (36): collect_local_outboxes(), _load_inbox_document(), load_local_inbox(), _load_outbox_document(), local_inbox_path(), local_outbox_path(), LocalTransportError, materialize_local_inboxes() (+28 more)

### Community 13 - "Community 13"
Cohesion: 0.11
Nodes (22): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), _load_manifest_document(), load_manifest_jobs(), LocalJobBatch, ManifestError, _parse_capabilities() (+14 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (80): Counter, _accepted_result(), aggregate_local_flow(), AggregationError, build_local_flow_aggregate(), _is_accepted(), Any, Path (+72 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (31): detectPython(), { execFile }, execFileAsync, isUsablePythonVersion(), parsePythonVersion(), { promisify }, runVersion(), getAetherMeshPaths() (+23 more)

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (20): build_collected_outbox_message_log_document(), build_flow_message_log_document(), build_message_log_document(), build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages(), load_worker_emitted_messages(), _message_to_document_entry() (+12 more)

### Community 17 - "Community 17"
Cohesion: 0.27
Nodes (19): CompletedProcess, changed_pyproject_from_base(), command_artifact_provenance(), command_dependency_audit(), command_dependency_review(), command_mutation_score(), command_pr_size(), command_test_integrity() (+11 more)

### Community 18 - "Community 18"
Cohesion: 0.08
Nodes (32): isDestroyedElectronObject(), isDestroyedError(), sendWindowState(), shouldLeaveBackgroundNodeRunning(), shouldStopTemporaryNode(), buildPackageInstallCommand(), DEFAULT_SETTINGS, normalizePackageSettings() (+24 more)

### Community 19 - "Community 19"
Cohesion: 0.11
Nodes (13): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Register a node ID or ScheduledNode in deterministic insertion order., Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order. (+5 more)

### Community 20 - "Community 20"
Cohesion: 0.13
Nodes (23): _config_api_host(), _config_api_port(), _config_enabled_work_types(), _config_identity_path(), _config_identity_persistence_enabled(), _config_node_id(), _config_node_name(), _merge_config() (+15 more)

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (32): callback, help, is_eager, Option, _background_mode_enabled(), _control_background_node(), init(), jobs() (+24 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (7): LocalScheduler, NoAvailableNodesError, ValueError, Raised when local job assignment has jobs but no available nodes., In-memory deterministic scheduler for local prototype jobs., Assign jobs to available capable nodes with deterministic fair ordering., LocalSchedulerTests

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (26): RuntimeError, build_parser(), format_duration(), format_progress_line(), main(), max_non_killed_for_score(), parse_mutmut_counts(), parse_mutmut_progress() (+18 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (20): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), LocalNodeService, Any, Synchronous local-only handler for one node's assigned-work inbox., Process unhandled ``job_assigned`` messages addressed to this node.          The, LocalSimulationResult, _node_roster_entry() (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (17): Run local file transport with workers discovered from heartbeat peers., run_peer_transport_flow(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Any (+9 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (14): AetherMesh Core Persistent Goal, AI Direction, Build Direction, Contribution Tracking Direction, Current Priority Bias, Decision Rule For Every Interval, Development Philosophy, Early Prototype Target (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (22): run_demo(), _canonical_root_json(), _component_hashes(), deterministic_machine_node_id(), deterministic_machine_node_name(), HardwareComponentHashes, HardwareIdentityInputs, _index_from_hash() (+14 more)

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (14): dispatch_local_batch_command(), InboxReplayRequest, _mark_ephemeral_message_log(), _node_ids_from_replayed_messages(), process_local_inbox(), Replay a saved local message log or local transport inbox for one node., Replay saved local messages and return payload plus structured result., Dispatch a manifest batch to a local message log without execution. (+6 more)

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (14): dispatch_peer_batch_command(), Dispatch manifest jobs to heartbeat-derived peers without execution., dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Any, Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary. (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.18
Nodes (11): atomic_create_json(), atomic_write_json(), _publish_json(), Any, Path, Shared JSON file persistence helpers for local-only artifacts., Write one JSON document using a temp file and atomic replace., Create one JSON document atomically without replacing an existing file. (+3 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (16): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Any, Path, ValueError, Versioned local node processing state persistence. (+8 more)

### Community 32 - "Community 32"
Cohesion: 0.11
Nodes (20): build_receipt_document(), Return validated metadata documents keyed by their stable reference., Build a deterministic version 1 receipt document.      Receipts are derived from, _version_metadata_documents(), capture_version_metadata(), _node_software_version(), ValueError, Return a stable local reference for one validated metadata document. (+12 more)

### Community 33 - "Community 33"
Cohesion: 0.15
Nodes (8): CLI and Local UI Architecture, Commands, Desktop launcher, Install, Local API, Local dashboard, Security default, Shape

### Community 35 - "Community 35"
Cohesion: 0.17
Nodes (11): _ensure_manifest_directories(), _identity_creator_node_id(), LocalStartupError, ValueError, Initialize one local node runtime without external services., Raised when local node startup cannot fail closed safely., start_local_node(), _validate_manifest() (+3 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (19): buildPosixShim(), buildShellPathBlock(), buildWindowsCmdShim(), buildWindowsPowerShellShim(), CliManager, { execFile: defaultExecFile }, execFilePromise(), fs (+11 more)

### Community 37 - "Community 37"
Cohesion: 0.09
Nodes (10): HostnameReader, _default_goos(), _identity_document(), load_or_create_identity(), parse_local_node_identity_document(), Parse and validate the Phase 1 public local node identity shape., Load a versioned local node identity, creating one if the file is missing., _run_command() (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.18
Nodes (10): Capability listing response contract, Explicitly out of scope, Manifest and artifact contract, Node create/load contract, Phase 1 Local API Boundary, Scope and locality, Submission, acceptance, and rejection, Traceability rule and required planned binding (+2 more)

### Community 40 - "Community 40"
Cohesion: 0.12
Nodes (26): Enum, allowed_next_states(), canonical_lifecycle_states(), LifecycleRecord, LifecycleStateSpec, LifecycleTransitionError, LocalNodeLifecycleState, ValueError (+18 more)

### Community 41 - "Community 41"
Cohesion: 0.12
Nodes (30): configured_runtime_path(), configured_runtime_ref(), default_local_runtime_config(), load_local_runtime_config(), load_optional_local_runtime_config(), load_or_create_local_runtime_config(), LocalRuntimeConfigError, parse_local_runtime_config() (+22 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (35): _LocalError, append_json_line(), canonical_json_hash(), load_json_mapping(), Any, Path, Small JSON helpers shared by local lifecycle commands., Read a required JSON object and raise the caller's local error type. (+27 more)

### Community 43 - "Community 43"
Cohesion: 0.11
Nodes (26): LocalRuntimeConfig, One explicit local-only runtime config source for startup artifacts., _classify_startup_error(), _configured_path(), _contains_runtime_artifacts(), _default_manifest_document(), _document_hash(), _ensure_runtime_dirs() (+18 more)

### Community 44 - "Community 44"
Cohesion: 0.11
Nodes (29): _append_log(), _artifact_refs(), _document_hash(), _interrupted_work_refs(), _iter_files(), _load_json_object(), LocalShutdownError, LocalShutdownResult (+21 more)

### Community 45 - "Community 45"
Cohesion: 0.12
Nodes (33): _artifact_refs(), _attribution_id(), _error_summary(), inspect_local_node_runtime(), _lineage_parent(), _load_identity_and_manifest(), _load_latest_artifact(), _load_runtime_json() (+25 more)

### Community 46 - "Community 46"
Cohesion: 0.12
Nodes (29): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), ContributionRecord, Audit record derived from one local job result., InboxProcessResult, ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally., Structured result returned by one local inbox processing pass. (+21 more)

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (12): Assignment-only local dispatch for manifest-backed batches., MessageDelivery, Synchronous in-memory message bus for local AetherMesh simulation., A message accepted by the local bus with its deterministic sequence., JSON-backed local message log persistence for batch simulations., Local mesh message envelopes for deterministic simulation output., _require_non_empty_string(), _require_supported_message_type() (+4 more)

### Community 48 - "models.py"
Cohesion: 0.18
Nodes (9): AetherMesh Core local prototype package., Contribution ledger helpers for local job results., Core data models for the local AetherMesh prototype., Local-only node inbox processing service for assigned work messages., Canonical SHA-256 hashing for accounted local job results., _preferred_text_chunk_split(), Local in-memory runner for the first AetherMesh executable slice., Return a deterministic split point no later than ``hard_end``. (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.22
Nodes (7): _mark_ephemeral_artifact(), _node_artifact_filename(), _node_artifact_path(), Command-line interface for the local AetherMesh prototype., Return a deterministic, non-merging filename for one manifest node id., _require_int_result_field(), Locally observable software and runtime version metadata.

### Community 51 - "Community 51"
Cohesion: 0.39
Nodes (23): backgroundStateFromSettings(), bootstrap(), checkRuntimeUpdates(), cliStateFromSettings(), createBackgroundManager(), createCliManager(), disableBackgroundNode(), enableBackgroundNode() (+15 more)

### Community 52 - "Community 52"
Cohesion: 0.09
Nodes (21): electron, electron-builder, author, description, devDependencies, electron, electron-builder, main (+13 more)

### Community 53 - "Community 53"
Cohesion: 0.10
Nodes (19): AER — Adaptive Expert Routing, AetherMesh Core, AetherMesh Core Persistent Goal, ai/local-loop-20260702-072353-1, Architecture direction, Core Terms, Development approach, docs/persistent-goal.md excerpt (+11 more)

### Community 54 - "Community 54"
Cohesion: 0.10
Nodes (19): AER — Adaptive Expert Routing, AetherMesh Core, AetherMesh Core Persistent Goal, ai/local-loop-20260702-072353-1, Architecture direction, Core Terms, Development approach, docs/persistent-goal.md excerpt (+11 more)

### Community 55 - "Community 55"
Cohesion: 0.26
Nodes (19): build_parser(), build_release_metadata(), command_prepare(), Commit, commits_since(), format_release_notes(), head_sha(), main() (+11 more)

### Community 56 - "Community 56"
Cohesion: 0.06
Nodes (36): Load an existing ledger and return read-only aggregate totals., summarize_ledger(), ContributionLedger, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document(), load_ledger_document(), Any (+28 more)

### Community 57 - "Community 57"
Cohesion: 0.16
Nodes (9): _message_from_inbox_entry(), _message_from_document_entry(), MeshMessage, message_from_mapping(), Any, JSON-compatible message envelope for local mesh communication records., Serialize the message into a JSON-compatible dictionary., Build a validated MeshMessage from a JSON-like mapping. (+1 more)

### Community 58 - "release_update.py"
Cohesion: 0.22
Nodes (17): build_update_plan(), _checksum_for_asset(), _fetch_bytes(), _fetch_json(), _find_asset(), _install_wheel(), _optional_string_field(), Path (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.14
Nodes (14): AetherMesh CLI, AetherMesh Desktop, Background OS-managed mode, Deferred work, Development commands, Manual validation, Packaging targets, Runtime model (+6 more)

### Community 60 - "Community 60"
Cohesion: 0.31
Nodes (13): bootstrapState, els, formatBool(), refreshDashboard(), renderBackground(), renderCapabilities(), renderCli(), renderPeers() (+5 more)

### Community 61 - "Community 61"
Cohesion: 0.19
Nodes (12): build_keyword_extract_output(), build_text_chunk_output(), build_text_embed_output(), build_text_retrieve_output(), build_text_stats_output(), Any, Build deterministic text statistics for a local ``text_stats`` job., Build deterministic keyword counts for a local ``keyword_extract`` job. (+4 more)

### Community 62 - "Community 62"
Cohesion: 0.35
Nodes (12): _base_checks(), Check, _checks_for_mode(), _command_available(), _full_extra_checks(), _merged_env(), _missing_required_tools(), _python() (+4 more)

### Community 64 - "Community 64"
Cohesion: 0.17
Nodes (11): AetherMesh CLI, CLI shim paths, Linux, macOS, Manual tests, PATH setup, Repair CLI, Runtime updates (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.17
Nodes (12): AEF: Aether Expert Fabric, AER: Adaptive Expert Routing, AetherMesh Core Architecture, Contribution tracking direction, Core responsibilities, Current prototype layer, Decision rule for new work, Non-goals for the current prototype (+4 more)

### Community 66 - "Community 66"
Cohesion: 0.35
Nodes (4): Return capped integer contribution units for one validated local result.      Th, score_validated_contribution(), ContributionScoringTests, _run()

### Community 67 - "Desktop Troubleshooting"
Cohesion: 0.18
Nodes (10): API did not start, Bundled runtime missing, Desktop Troubleshooting, Development fallback, Linux `.deb` package metadata, Linux system dependency missing, macOS Gatekeeper, Node already running (+2 more)

### Community 68 - "Community 68"
Cohesion: 0.15
Nodes (7): _default_home(), _memory_total_bytes(), _pid_is_alive(), Path, Filesystem paths used by one local AetherMesh runtime., RuntimePaths, RuntimeServiceTests

### Community 69 - "Community 69"
Cohesion: 0.18
Nodes (10): args, built, entry, fs, nodeNameWordlists, path, result, root (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.24
Nodes (9): create_app(), _lifespan(), FastAPI, Local FastAPI app for the AetherMesh node dashboard., Create the localhost API/dashboard app used by CLI and UI frontends., ApiTests, _fetch_api_payloads(), Any (+1 more)

### Community 71 - "Community 71"
Cohesion: 0.49
Nodes (10): _cap_units(), _ceil_div(), _non_negative_int(), Any, Deterministic contribution scoring for validated local workload results., _score_keyword_extract(), _score_text_chunk(), _score_text_embed() (+2 more)

### Community 72 - "Community 72"
Cohesion: 0.22
Nodes (9): _accounted_units(), ValueError, Record one result and return its local contribution record.          Only comple, _string_output(), _fallback_job_id(), _job_from_assignment_payload(), _coerce_job(), Minimal scheduler view of a job. (+1 more)

### Community 74 - "REVA Pipeline"
Cohesion: 0.25
Nodes (8): AEF — Aether Expert Fabric, AER — Adaptive Expert Routing, Aggregator, Core Terms, Expert, REVA Pipeline, Router, Validator

### Community 75 - "Community 75"
Cohesion: 0.29
Nodes (6): Background Node Manual Test Plan, Linux systemd user service, macOS LaunchAgent, Runtime update checks, Shared checks, Windows Task Scheduler

### Community 76 - "Community 76"
Cohesion: 0.08
Nodes (31): NodeIdFactory, _append_identity_reset_receipt(), _backup_identity_referenced_artifacts(), _create_identity_document_without_overwrite(), _identity_document_creator_node_id(), _identity_reset_artifact_ref(), _identity_reset_warning(), IdentityPersistenceError (+23 more)

### Community 77 - "Community 77"
Cohesion: 0.33
Nodes (5): fs, path, root, target, targetDir

### Community 78 - "Community 78"
Cohesion: 0.29
Nodes (7): Local Node Identity Format, Local prototype reset procedure, Manifest linkage, Minimal example, Private key material, Version 1 document shape, Versioning rules

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (6): AetherMesh alignment, Follow-ups, Objective, Safety notes, Validation, What changed

### Community 82 - "Community 82"
Cohesion: 0.53
Nodes (5): fs, getBundledRuntimePath(), getRuntimeExecutableName(), path, resolveRuntimeCommand()

### Community 83 - "Community 83"
Cohesion: 0.40
Nodes (5): Aggregator, Expert, REVA pipeline, Router, Validator

### Community 84 - "Community 84"
Cohesion: 0.33
Nodes (6): Canonical states, Local Node Lifecycle, Persisted fields for lifecycle-changing events, Restart recovery, Scope boundaries, Transition events and validation conditions

### Community 85 - "Community 85"
Cohesion: 0.50
Nodes (3): IdentityResetResult, Local audit details for an explicit identity reset., Return JSON-serializable reset details for CLI/API callers.

### Community 86 - "Community 86"
Cohesion: 0.50
Nodes (3): LocalNodeIdentity, Validated version 1 public local node identity document., Return the public identity document without private key material.

### Community 87 - "Community 87"
Cohesion: 0.30
Nodes (3): _new_local_node_id(), _node_name_wordlist_dir(), Return a legacy collision-resistant local node id for explicit rotations.

### Community 88 - "Community 88"
Cohesion: 0.40
Nodes (4): main, name, private, version

## Knowledge Gaps
- **235 isolated node(s):** `name`, `version`, `private`, `main`, `{ spawnSync }` (+230 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MeshMessage` connect `Community 57` to `Community 32`, `Community 1`, `Community 2`, `Community 5`, `Community 72`, `Community 8`, `Community 12`, `Community 46`, `Community 14`, `Community 47`, `Community 16`, `Community 24`, `Community 25`, `Community 28`, `Community 29`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `NodeIdentity` connect `Community 0` to `Community 32`, `Community 66`, `Community 2`, `Community 68`, `Community 37`, `Community 6`, `Community 72`, `Community 10`, `Community 76`, `Community 46`, `models.py`, `Community 20`, `Community 85`, `Community 86`, `Community 24`, `Community 27`, `Community 28`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `main()` connect `Community 14` to `Community 1`, `Community 35`, `release_update.py`, `Community 76`, `Community 13`, `Community 12`, `Community 46`, `Community 16`, `Community 49`, `Community 45`, `Community 24`, `Community 25`, `Community 56`, `Community 27`, `Community 28`, `Community 29`, `Community 31`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 111 inferred relationships involving `Job` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`Job` has 111 INFERRED edges - model-reasoned connections that need verification._
- **Are the 93 inferred relationships involving `main()` (e.g. with `.test_aggregate_local_flow_audit_failure_returns_nonzero_without_writing()` and `.test_aggregate_local_flow_writes_artifact_and_prints_summary()`) actually correct?**
  _`main()` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Are the 44 inferred relationships involving `MeshMessage` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`MeshMessage` has 44 INFERRED edges - model-reasoned connections that need verification._
- **Are the 62 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 62 INFERRED edges - model-reasoned connections that need verification._