# Graph Report - aethermesh-core  (2026-07-11)

## Corpus Check
- 137 files · ~180,769 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2279 nodes · 5994 edges · 103 communities (86 shown, 17 thin omitted)
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 1658 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ffc6b3b2`
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
- load_full_test_module
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
- LocalApiClient
- Community 88
- runtime.js
- Community 90
- Community 92
- Community 94
- .__post_init__
- clean.js
- Community 97
- preload.js
- MessageDelivery
- Community 100
- Community 101
- Community 102

## God Nodes (most connected - your core abstractions)
1. `Job` - 155 edges
2. `main()` - 97 edges
3. `MeshMessage` - 97 edges
4. `JobResult` - 89 edges
5. `NodeIdentity` - 80 edges
6. `IdentityPersistenceTests` - 73 edges
7. `CliTests` - 72 edges
8. `start_local_node()` - 67 edges
9. `IdentityPersistenceError` - 64 edges
10. `LocalRunner` - 53 edges

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

## Communities (103 total, 17 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.15
Nodes (7): NodeIdentity, Identity for one local node., LocalRunner, Execute supported local job types for a node., Raised when a requested local validation receipt is not stored., ValidationReceiptNotFoundError, LocalRunnerTests

### Community 1 - "Community 1"
Cohesion: 0.20
Nodes (17): CapabilityRecordError, Any, ValueError, Validation for versioned, local-only capability records., Raised when a local capability record is incomplete or unsafe., Validate and copy one local-only capability record version 1.      This checks r, _require_exact_keys(), _require_identifier() (+9 more)

### Community 2 - "Community 2"
Cohesion: 0.12
Nodes (37): collect_local_outboxes(), _load_inbox_document(), load_local_inbox(), _load_outbox_document(), local_inbox_path(), local_outbox_path(), LocalTransportError, materialize_local_inboxes() (+29 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (12): Return capped integer contribution units for one validated local result.      Th, score_validated_contribution(), Job, JobResult, A small in-memory job assigned to a local node., Structured result emitted after local job execution., _invalid(), Validate a reported result against the assigned local job.      The current prot (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.20
Nodes (10): AetherMesh Core, Current status, Development principles, Documentation, Install for development, License, Prototype flow examples, Quick start (+2 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (19): NodeRuntimeService, Path, ValueError, Raised when local runtime state cannot be safely loaded or written., Filesystem paths used by one local AetherMesh runtime., Run a queued local submission; this is not a daemon or remote boundary., Central service for local node config, lifecycle status, peers, and jobs., Allow readable local identifiers while rejecting path and URI-shaped values. (+11 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (15): BackgroundNodeManager, buildLaunchAgentPlist(), buildSystemdUserService(), buildWindowsTaskXml(), crypto, { execFile: defaultExecFile }, execFilePromise(), fs (+7 more)

### Community 7 - "Community 7"
Cohesion: 0.07
Nodes (27): shouldLeaveBackgroundNodeRunning(), shouldStopTemporaryNode(), getAetherMeshPaths(), getDefaultAetherMeshHome(), getDefaultAetherMeshLogsDir(), os, path, buildCreateVenvCommand() (+19 more)

### Community 10 - "Community 10"
Cohesion: 0.05
Nodes (50): callback, help, is_eager, Option, _background_mode_enabled(), _control_background_node(), init(), jobs() (+42 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (51): CommandRunner, FileReader, _bytes_to_gb(), collect_hardware_identity_inputs(), _colon_value(), _count_display_chips(), _csv_first_value(), _darwin_hardware_inputs() (+43 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (29): isDestroyedElectronObject(), isDestroyedError(), sendWindowState(), buildPackageInstallCommand(), DEFAULT_SETTINGS, normalizePackageSettings(), apiClient, { app, BrowserWindow, ipcMain } (+21 more)

### Community 13 - "Community 13"
Cohesion: 0.12
Nodes (19): buildPosixShim(), buildShellPathBlock(), buildWindowsCmdShim(), buildWindowsPowerShellShim(), CliManager, { execFile: defaultExecFile }, execFilePromise(), fs (+11 more)

### Community 14 - "Community 14"
Cohesion: 0.07
Nodes (68): Counter, _accepted_result(), aggregate_local_flow(), AggregationError, build_local_flow_aggregate(), _is_accepted(), Any, Path (+60 more)

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (25): _contains_secret_identity_fragment(), _identity_artifact_has_identity_metadata(), _identity_artifact_mentions_node(), _identity_document_creator_node_id(), IdentityPersistenceError, _load_identity(), _load_identity_document(), _manifest_document_matches_node() (+17 more)

### Community 16 - "Community 16"
Cohesion: 0.09
Nodes (27): build_collected_outbox_message_log_document(), build_dispatch_message_log_document(), build_flow_message_log_document(), build_message_log_document(), build_replayed_message_log_document(), _load_message_log_document(), load_message_log_messages(), load_worker_emitted_messages() (+19 more)

### Community 17 - "Community 17"
Cohesion: 0.27
Nodes (19): CompletedProcess, changed_pyproject_from_base(), command_artifact_provenance(), command_dependency_audit(), command_dependency_review(), command_mutation_score(), command_pr_size(), command_test_integrity() (+11 more)

### Community 18 - "Community 18"
Cohesion: 0.12
Nodes (30): configured_runtime_path(), configured_runtime_ref(), default_local_runtime_config(), load_local_runtime_config(), load_optional_local_runtime_config(), load_or_create_local_runtime_config(), LocalRuntimeConfigError, parse_local_runtime_config() (+22 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (8): NodeRegistry, In-memory source of truth for local simulation node state.      The registry is, Mark a known node available for future scheduler exports., Mark a known node offline for future scheduler exports., Record one deterministic local heartbeat for a known node., Return scheduler-compatible nodes in registration order., Return JSON-compatible roster entries in registration order., NodeRegistryTests

### Community 20 - "Community 20"
Cohesion: 0.26
Nodes (19): build_parser(), build_release_metadata(), command_prepare(), Commit, commits_since(), format_release_notes(), head_sha(), main() (+11 more)

### Community 21 - "Community 21"
Cohesion: 0.10
Nodes (25): LocalRuntimeConfig, One explicit local-only runtime config source for startup artifacts., _classify_startup_error(), _configured_path(), _contains_runtime_artifacts(), _default_manifest_document(), _document_hash(), _ensure_runtime_dirs() (+17 more)

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (10): _coerce_node(), LocalScheduler, NoAvailableNodesError, ValueError, Raised when local job assignment has jobs but no available nodes., Local scheduler view of a node., In-memory deterministic scheduler for local prototype jobs., Assign jobs to available capable nodes with deterministic fair ordering. (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.19
Nodes (18): build_parser(), format_duration(), format_progress_line(), main(), max_non_killed_for_score(), parse_mutmut_counts(), parse_mutmut_progress(), ArgumentParser (+10 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (20): Run the fixed local simulation demo used by the CLI command., run_default_local_simulation(), LocalNodeService, Any, Synchronous local-only handler for one node's assigned-work inbox., Process unhandled ``job_assigned`` messages addressed to this node.          The, LocalSimulationResult, _node_roster_entry() (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.14
Nodes (16): Load an existing message log and return a read-only peer roster., summarize_peers(), _parse_capabilities(), _parse_heartbeat(), peer_summary_document(), PeerRegistryError, PeerSummary, Any (+8 more)

### Community 26 - "Community 26"
Cohesion: 0.14
Nodes (14): AetherMesh Core Persistent Goal, AI Direction, Build Direction, Contribution Tracking Direction, Current Priority Bias, Decision Rule For Every Interval, Development Philosophy, Early Prototype Target (+6 more)

### Community 27 - "Community 27"
Cohesion: 0.11
Nodes (18): _canonical_root_json(), _component_hashes(), deterministic_machine_node_id(), deterministic_machine_node_name(), HardwareComponentHashes, _index_from_hash(), _node_name_from_hashes(), _node_name_wordlists() (+10 more)

### Community 28 - "Community 28"
Cohesion: 0.11
Nodes (19): announce_local_node(), build_node_announcement_message_log_document(), build_node_heartbeat_message(), NodeAnnouncementError, normalize_announcement_capabilities(), Any, Path, ValueError (+11 more)

### Community 29 - "Community 29"
Cohesion: 0.16
Nodes (23): AssignmentKey, _assignment_key(), _job_from_assignment(), LocalValidationError, Any, Path, ValueError, Independent local replay validation for reported AetherMesh job results. (+15 more)

### Community 30 - "Community 30"
Cohesion: 0.18
Nodes (12): atomic_create_json(), atomic_write_json(), _publish_json(), Any, Path, Shared JSON file persistence helpers for local-only artifacts., Write one JSON document using a temp file and atomic replace., Create one JSON document atomically without replacing an existing file. (+4 more)

### Community 31 - "Community 31"
Cohesion: 0.13
Nodes (16): empty_node_processing_state(), load_node_processing_state(), LocalNodeProcessingState, NodeStatePersistenceError, Any, Path, ValueError, Versioned local node processing state persistence. (+8 more)

### Community 32 - "Community 32"
Cohesion: 0.12
Nodes (30): ProcessedAssignment, Deterministic audit data for one inbox assignment processed locally., build_receipt_document(), _json_compatible_dict(), _json_compatible_list(), _json_compatible_value(), load_receipt_document_if_exists(), _output_summary() (+22 more)

### Community 33 - "Community 33"
Cohesion: 0.25
Nodes (8): CLI and Local UI Architecture, Commands, Desktop launcher, Install, Local API, Local dashboard, Security default, Shape

### Community 35 - "Community 35"
Cohesion: 0.17
Nodes (11): _ensure_manifest_directories(), _identity_creator_node_id(), LocalStartupError, ValueError, Initialize one local node runtime without external services., Raised when local node startup cannot fail closed safely., start_local_node(), _validate_manifest() (+3 more)

### Community 36 - "Community 36"
Cohesion: 0.39
Nodes (23): backgroundStateFromSettings(), bootstrap(), checkRuntimeUpdates(), cliStateFromSettings(), createBackgroundManager(), createCliManager(), disableBackgroundNode(), enableBackgroundNode() (+15 more)

### Community 37 - "Community 37"
Cohesion: 0.10
Nodes (10): HostnameReader, _identity_document(), load_or_create_identity(), _new_local_node_id(), Load a versioned local node identity, creating one if the file is missing., Return a legacy collision-resistant local node id for explicit rotations., _run_command(), _save_identity() (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (19): Local API error envelope, Local Contribution Lookup v1, Local Job Status v1, Local Job Submission v1, Local Validation Receipt v1, Phase 1 API Schema Contract, Route index, Validation receipt (+11 more)

### Community 40 - "Community 40"
Cohesion: 0.13
Nodes (25): allowed_next_states(), canonical_lifecycle_states(), LifecycleRecord, LifecycleStateSpec, LifecycleTransitionError, LocalNodeLifecycleState, ValueError, Local-first lifecycle model for one AetherMesh node runtime. (+17 more)

### Community 41 - "Community 41"
Cohesion: 0.10
Nodes (19): AER — Adaptive Expert Routing, AetherMesh Core, AetherMesh Core Persistent Goal, ai/local-loop-20260702-072353-1, Architecture direction, Core Terms, Development approach, docs/persistent-goal.md excerpt (+11 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (35): _LocalError, append_json_line(), canonical_json_hash(), load_json_mapping(), Any, Path, Small JSON helpers shared by local lifecycle commands., Read a required JSON object and raise the caller's local error type. (+27 more)

### Community 43 - "Community 43"
Cohesion: 0.10
Nodes (14): LocalMessageBus, Any, Dependency-free local-only message bus for deterministic simulations., Register a node or reserved local service actor with the bus., Accept a message from a registered sender to a registered recipient., Return a copy of the ordered message log., Return a copy of the deterministic inbox for a registered node., Create and send a message with the next deterministic bus sequence id. (+6 more)

### Community 44 - "Community 44"
Cohesion: 0.11
Nodes (29): _append_log(), _artifact_refs(), _document_hash(), _interrupted_work_refs(), _iter_files(), _load_json_object(), LocalShutdownError, LocalShutdownResult (+21 more)

### Community 45 - "Community 45"
Cohesion: 0.12
Nodes (33): _artifact_refs(), _attribution_id(), _error_summary(), inspect_local_node_runtime(), _lineage_parent(), _load_identity_and_manifest(), _load_latest_artifact(), _load_runtime_json() (+25 more)

### Community 46 - "Community 46"
Cohesion: 0.19
Nodes (11): _emitted_messages_from_inbox_result(), _inbox_process_result_to_dict(), InboxReplayRequest, _fallback_job_id(), InboxProcessResult, _job_from_assignment_payload(), Structured result returned by one local inbox processing pass., _coerce_job() (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.10
Nodes (22): Run a local simulation from a validated JSON manifest., run_local_batch(), load_job_manifest(), _load_manifest_document(), load_manifest_jobs(), LocalJobBatch, ManifestError, _parse_capabilities() (+14 more)

### Community 48 - "models.py"
Cohesion: 0.18
Nodes (10): AetherMesh Core local prototype package., Contribution ledger helpers for local job results., Synchronous in-memory message bus for local AetherMesh simulation., Local mesh message envelopes for deterministic simulation output., Core data models for the local AetherMesh prototype., Local-only node inbox processing service for assigned work messages., Canonical SHA-256 hashing for accounted local job results., Local in-memory runner for the first AetherMesh executable slice. (+2 more)

### Community 49 - "Community 49"
Cohesion: 0.10
Nodes (19): AER — Adaptive Expert Routing, AetherMesh Core, AetherMesh Core Persistent Goal, ai/local-loop-20260702-072353-1, Architecture direction, Core Terms, Development approach, docs/persistent-goal.md excerpt (+11 more)

### Community 51 - "Community 51"
Cohesion: 0.13
Nodes (16): dispatch_local_batch_command(), dispatch_peer_batch_command(), _log_ephemeral_identity_active(), main(), _mark_ephemeral_message_log(), _node_ids_from_replayed_messages(), process_local_inbox(), Replay a saved local message log or local transport inbox for one node. (+8 more)

### Community 52 - "Community 52"
Cohesion: 0.09
Nodes (21): electron, electron-builder, author, description, devDependencies, electron, electron-builder, main (+13 more)

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (13): build_parser(), _node_artifact_filename(), _node_artifact_path(), ArgumentParser, Exception, Path, Command-line interface for the local AetherMesh prototype., Return a deterministic, non-merging filename for one manifest node id. (+5 more)

### Community 54 - "Community 54"
Cohesion: 0.08
Nodes (21): NodeIdFactory, _append_identity_reset_receipt(), _backup_identity_referenced_artifacts(), _create_identity_document_without_overwrite(), _identity_reset_artifact_ref(), _identity_reset_warning(), IdentityResetResult, _load_identity_reset_receipts() (+13 more)

### Community 55 - "Community 55"
Cohesion: 0.23
Nodes (4): Assignment-only local dispatch for manifest-backed batches., Deterministic local node registry for simulation roster state., Read-only local peer roster derived from heartbeat messages., Deterministic local scheduler for the AetherMesh prototype.

### Community 56 - "Community 56"
Cohesion: 0.06
Nodes (37): _mark_ephemeral_artifact(), run_demo(), _accounted_units(), ContributionLedger, ContributionRecord, ContributionSummary, LedgerPersistenceError, load_existing_ledger_document() (+29 more)

### Community 57 - "Community 57"
Cohesion: 0.17
Nodes (7): MeshMessage, message_from_mapping(), Any, JSON-compatible message envelope for local mesh communication records., Serialize the message into a JSON-compatible dictionary., Build a validated MeshMessage from a JSON-like mapping., MeshMessageTests

### Community 58 - "release_update.py"
Cohesion: 0.13
Nodes (23): _config_api_host(), _config_api_port(), _config_enabled_work_types(), _config_identity_path(), _config_identity_persistence_enabled(), _config_node_id(), _config_node_name(), _default_home() (+15 more)

### Community 59 - "Community 59"
Cohesion: 0.19
Nodes (8): dispatch_local_batch(), LocalDispatchResult, _node_heartbeat_payloads(), Any, Structured result for local assignment-only dispatch., Serialize a deterministic, intentionally small CLI summary., Build a local dispatch log with heartbeats and job assignments only.      This f, DispatchTests

### Community 60 - "Community 60"
Cohesion: 0.14
Nodes (14): AetherMesh CLI, AetherMesh Desktop, Background OS-managed mode, Deferred work, Development commands, Manual validation, Packaging targets, Runtime model (+6 more)

### Community 61 - "Community 61"
Cohesion: 0.31
Nodes (13): bootstrapState, els, formatBool(), refreshDashboard(), renderBackground(), renderCapabilities(), renderCli(), renderPeers() (+5 more)

### Community 62 - "Community 62"
Cohesion: 0.35
Nodes (12): _base_checks(), Check, _checks_for_mode(), _command_available(), _full_extra_checks(), _merged_env(), _missing_required_tools(), _python() (+4 more)

### Community 64 - "Community 64"
Cohesion: 0.19
Nodes (12): build_keyword_extract_output(), build_text_chunk_output(), build_text_embed_output(), build_text_retrieve_output(), build_text_stats_output(), Any, Build deterministic text statistics for a local ``text_stats`` job., Build deterministic keyword counts for a local ``keyword_extract`` job. (+4 more)

### Community 65 - "Community 65"
Cohesion: 0.17
Nodes (12): AEF: Aether Expert Fabric, AER: Adaptive Expert Routing, AetherMesh Core Architecture, Contribution tracking direction, Core responsibilities, Current prototype layer, Decision rule for new work, Non-goals for the current prototype (+4 more)

### Community 66 - "Community 66"
Cohesion: 0.17
Nodes (11): AetherMesh CLI, CLI shim paths, Linux, macOS, Manual tests, PATH setup, Repair CLI, Runtime updates (+3 more)

### Community 67 - "Desktop Troubleshooting"
Cohesion: 0.18
Nodes (10): API did not start, Bundled runtime missing, Desktop Troubleshooting, Development fallback, Linux `.deb` package metadata, Linux system dependency missing, macOS Gatekeeper, Node already running (+2 more)

### Community 69 - "Community 69"
Cohesion: 0.18
Nodes (10): args, built, entry, fs, nodeNameWordlists, path, result, root (+2 more)

### Community 70 - "Community 70"
Cohesion: 0.49
Nodes (10): _cap_units(), _ceil_div(), _non_negative_int(), Any, Deterministic contribution scoring for validated local workload results., _score_keyword_extract(), _score_text_chunk(), _score_text_embed() (+2 more)

### Community 71 - "Community 71"
Cohesion: 0.33
Nodes (5): Local Capability Record Schema, Metadata and manifests, Required top-level fields, Valid example, Validation, lineage, and attribution

### Community 73 - "Community 73"
Cohesion: 0.33
Nodes (3): _ephemeral_roster(), Create a caller-usable ephemeral identity for local demo runs., NodeIdentityTests

### Community 74 - "REVA Pipeline"
Cohesion: 0.25
Nodes (8): AEF — Aether Expert Fabric, AER — Adaptive Expert Routing, Aggregator, Core Terms, Expert, REVA Pipeline, Router, Validator

### Community 75 - "Community 75"
Cohesion: 0.28
Nodes (5): _canonical_json_bytes(), Any, Hash the canonical result fields used by result messages and audits., result_hash_from_fields(), ResultHashTests

### Community 76 - "load_full_test_module"
Cohesion: 0.36
Nodes (3): FullTestRunnerTests, load_full_test_module(), ModuleType

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
Cohesion: 0.32
Nodes (4): DesktopReleaseWorkflowTests, load_quality_gates_module(), ModuleType, WorkflowSecurityTests

### Community 82 - "Community 82"
Cohesion: 0.29
Nodes (6): Background Node Manual Test Plan, Linux systemd user service, macOS LaunchAgent, Runtime update checks, Shared checks, Windows Task Scheduler

### Community 83 - "Community 83"
Cohesion: 0.40
Nodes (5): Aggregator, Expert, REVA pipeline, Router, Validator

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (6): Canonical states, Local Node Lifecycle, Persisted fields for lifecycle-changing events, Restart recovery, Scope boundaries, Transition events and validation conditions

### Community 85 - "Community 85"
Cohesion: 0.33
Nodes (6): Enum, Register a node ID or ScheduledNode in deterministic insertion order., _RegistryNode, NodeStatus, Availability states needed by the local scheduler., str

### Community 86 - "Community 86"
Cohesion: 0.33
Nodes (5): fs, path, root, target, targetDir

### Community 88 - "Community 88"
Cohesion: 0.40
Nodes (4): main, name, private, version

### Community 89 - "runtime.js"
Cohesion: 0.53
Nodes (5): fs, getBundledRuntimePath(), getRuntimeExecutableName(), path, resolveRuntimeCommand()

### Community 92 - "Community 92"
Cohesion: 0.17
Nodes (13): capture_version_metadata(), _node_software_version(), ValueError, Locally observable software and runtime version metadata., Raised when local version metadata is missing or malformed., Return factual local software/runtime metadata for one node run., Validate and return a shallow copy of a version metadata document., _require_non_empty_string() (+5 more)

### Community 94 - "Community 94"
Cohesion: 0.50
Nodes (3): LocalNodeIdentity, Validated version 1 public local node identity document., Return the public identity document without private key material.

### Community 95 - ".__post_init__"
Cohesion: 0.67
Nodes (3): _require_non_empty_string(), _require_supported_message_type(), _validate_json_compatible()

### Community 101 - "Community 101"
Cohesion: 0.11
Nodes (19): JSONResponse, Request, RuntimeError, create_app(), _error_response(), _lifespan(), FastAPI, Local FastAPI app for the AetherMesh node dashboard. (+11 more)

## Knowledge Gaps
- **247 isolated node(s):** `name`, `version`, `private`, `main`, `{ spawnSync }` (+242 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MeshMessage` connect `Community 57` to `Community 32`, `Community 2`, `MessageDelivery`, `Community 8`, `Community 43`, `Community 46`, `Community 14`, `Community 16`, `models.py`, `Community 24`, `Community 25`, `Community 59`, `Community 28`, `Community 29`, `.__post_init__`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `Job` connect `Community 3` to `Community 32`, `Community 0`, `Community 64`, `Community 5`, `Community 46`, `Community 47`, `Community 16`, `models.py`, `Community 51`, `Community 22`, `Community 24`, `Community 56`, `Community 59`, `Community 29`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `NodeIdentity` connect `Community 0` to `Community 32`, `Community 3`, `Community 37`, `Community 5`, `Community 73`, `Community 11`, `Community 43`, `Community 46`, `Community 15`, `models.py`, `Community 51`, `Community 54`, `Community 56`, `Community 24`, `release_update.py`, `Community 27`, `Community 92`, `Community 94`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 116 inferred relationships involving `Job` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`Job` has 116 INFERRED edges - model-reasoned connections that need verification._
- **Are the 93 inferred relationships involving `main()` (e.g. with `.test_aggregate_local_flow_audit_failure_returns_nonzero_without_writing()` and `.test_aggregate_local_flow_writes_artifact_and_prints_summary()`) actually correct?**
  _`main()` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Are the 44 inferred relationships involving `MeshMessage` (e.g. with `InboxReplayRequest` and `LocalDispatchResult`) actually correct?**
  _`MeshMessage` has 44 INFERRED edges - model-reasoned connections that need verification._
- **Are the 62 inferred relationships involving `JobResult` (e.g. with `ContributionLedger` and `ContributionRecord`) actually correct?**
  _`JobResult` has 62 INFERRED edges - model-reasoned connections that need verification._