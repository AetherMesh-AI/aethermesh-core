"""Reusable local runtime service for AetherMesh frontends.

The CLI, local API, and local dashboard all use this module instead of owning
node status logic independently. It is intentionally small and localhost-first:
it manages local config/data paths, identity initialization, status reporting,
and honest empty peer/job views for the current local-only prototype.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from aethermesh_core.identity import (
    deterministic_machine_node_id,
    deterministic_machine_node_name,
    load_or_create_identity,
)
from aethermesh_core.json_io import atomic_create_json, atomic_write_json
from aethermesh_core.models import Job, NodeIdentity
from aethermesh_core.runner import LocalRunner
from aethermesh_core.validation import validate_job_result

CONFIG_SCHEMA_VERSION = 1
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 7280
DEFAULT_LOCAL_CAPABILITIES = (
    "echo",
    "keyword_extract",
    "text_chunk",
    "text_embed",
    "text_stats",
)
PUBLIC_VERSION = "0.2.0-alpha"
CAPABILITY_LIST_SCHEMA_VERSION = 1
VALIDATION_RECEIPT_ID_PREFIX = "local-validation-receipt-"

# These definitions are the local runtime's source of truth. A configured work
# type is enabled only when it is registered here; provenance entries describe
# the local artifact contracts implemented by the Phase 1 runtime.
LOCAL_CAPABILITY_DEFINITIONS = (
    ("work.echo", "Run deterministic local echo jobs.", "echo"),
    (
        "work.keyword_extract",
        "Run deterministic local keyword extraction jobs.",
        "keyword_extract",
    ),
    ("work.text_chunk", "Run deterministic local text chunking jobs.", "text_chunk"),
    (
        "work.text_embed",
        "Run deterministic local text embedding helper jobs.",
        "text_embed",
    ),
    ("work.text_stats", "Run deterministic local text statistics jobs.", "text_stats"),
)
LOCAL_PROVENANCE_CAPABILITY_DEFINITIONS = (
    (
        "provenance.creator_node_id",
        "Preserve a creator node ID in local runtime identity artifacts.",
        "enabled",
    ),
    (
        "provenance.manifest",
        "Create and validate local startup and batch manifests.",
        "enabled",
    ),
    (
        "provenance.validation_receipt",
        "Write local validation receipts; these are not consensus evidence.",
        "enabled",
    ),
    (
        "provenance.lineage_reference",
        "Write and inspect local startup lineage references.",
        "enabled",
    ),
    (
        "provenance.contribution_attribution",
        "Record local validation-gated contribution attribution fields.",
        "enabled",
    ),
    (
        "provenance.end_to_end_runtime_lineage",
        "Bind a flow receipt to preserved creator and startup lineage evidence.",
        "disabled",
    ),
)


class RuntimeServiceError(ValueError):
    """Raised when local runtime state cannot be safely loaded or written."""


class ValidationReceiptNotFoundError(RuntimeServiceError):
    """Raised when a requested local validation receipt is not stored."""


@dataclass(frozen=True)
class RuntimePaths:
    """Filesystem paths used by one local AetherMesh runtime."""

    home: Path
    config_path: Path
    data_dir: Path
    log_dir: Path
    identity_path: Path
    pid_path: Path
    events_path: Path

    @classmethod
    def from_home(cls, home: str | Path) -> "RuntimePaths":
        root = Path(home).expanduser()
        return cls(
            home=root,
            config_path=root / "config.json",
            data_dir=root / "data",
            log_dir=root / "logs",
            identity_path=root / "identity.json",
            pid_path=root / "node.pid",
            events_path=root / "logs" / "events.log",
        )


class NodeRuntimeService:
    """Central service for local node config, lifecycle status, peers, and jobs."""

    def __init__(self, paths: RuntimePaths) -> None:
        self.paths = paths

    @classmethod
    def default(cls) -> "NodeRuntimeService":
        return cls.from_home(_default_home())

    @classmethod
    def from_home(cls, home: str | Path) -> "NodeRuntimeService":
        return cls(RuntimePaths.from_home(home))

    def load_config(self) -> dict[str, Any]:
        """Load local node config, returning a default view when missing."""

        if not self.paths.config_path.exists():
            return self._default_config(node_id=None)
        try:
            with self.paths.config_path.open("r", encoding="utf-8") as handle:
                document = json.load(handle)
        except json.JSONDecodeError as exc:
            raise RuntimeServiceError(f"config JSON is malformed: {exc.msg}") from exc
        except OSError as exc:
            raise RuntimeServiceError(f"could not read config file: {exc}") from exc
        if not isinstance(document, dict):
            raise RuntimeServiceError("config JSON must be an object")
        if document.get("version") != CONFIG_SCHEMA_VERSION:
            raise RuntimeServiceError("config JSON must contain version 1")
        return document

    def initialize_local_node_data(self) -> dict[str, Any]:
        """Create local runtime directories, identity, config, and log seed data."""

        self.paths.home.mkdir(parents=True, exist_ok=True)
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.log_dir.mkdir(parents=True, exist_ok=True)
        existing = self.load_config() if self.paths.config_path.exists() else None
        base_config = existing or self._default_config(node_id=None)
        persistence_enabled = _config_identity_persistence_enabled(base_config)
        identity_path = _config_identity_path(base_config, self.paths.identity_path)
        if persistence_enabled:
            identity = load_or_create_identity(identity_path)
        else:
            node_id = deterministic_machine_node_id()
            identity = NodeIdentity(
                node_id=node_id,
                node_name=deterministic_machine_node_name(node_id=node_id),
            )
        node_name = identity.node_name or deterministic_machine_node_name(
            node_id=identity.node_id
        )
        config = self._default_config(node_id=identity.node_id, node_name=node_name)
        if existing is not None:
            config = _merge_config(existing, config)
            config.setdefault("node", {})["node_id"] = identity.node_id
            config.setdefault("node", {})["node_name"] = node_name
        config.setdefault("identity", {})["persist"] = persistence_enabled
        config.setdefault("identity", {})["path"] = str(identity_path)
        self._write_config(config)
        if not self.paths.events_path.exists():
            self.paths.events_path.write_text("", encoding="utf-8")
        self._append_event("initialized local node data")
        return {
            "initialized": True,
            "node_id": identity.node_id,
            "node_name": node_name,
            "home": str(self.paths.home),
            "config_path": str(self.paths.config_path),
            "data_dir": str(self.paths.data_dir),
            "log_dir": str(self.paths.log_dir),
            "identity_path": str(identity_path),
            "identity_persisted": persistence_enabled,
        }

    def get_node_status(self) -> dict[str, Any]:
        """Return an honest local node status snapshot."""

        config = self.load_config()
        node_id = _config_node_id(config)
        node_name = _config_node_name(config)
        running, pid, started_at = self._runtime_marker()
        uptime_seconds: int | None = None
        if running and started_at is not None:
            uptime_seconds = max(0, int(time.time() - started_at))
        jobs = self.list_jobs()
        peers = self.list_peers()
        return {
            "initialized": self.paths.config_path.exists()
            and (
                not _config_identity_persistence_enabled(config)
                or _config_identity_path(config, self.paths.identity_path).exists()
            ),
            "node_id": node_id,
            "node_name": node_name,
            "status": "running" if running else "stopped",
            "version": _package_version(),
            "uptime_seconds": uptime_seconds,
            "pid": pid if running else None,
            "config_path": str(self.paths.config_path),
            "data_dir": str(self.paths.data_dir),
            "log_dir": str(self.paths.log_dir),
            "api": {
                "host": _config_api_host(config),
                "port": _config_api_port(config),
                "localhost_only": _config_api_host(config)
                in {"127.0.0.1", "localhost"},
            },
            "peer_count": len(peers["peers"]),
            "job_counts": {
                "current": len(jobs["current"]),
                "completed": len(jobs["completed"]),
                "failed": len(jobs["failed"]),
            },
            "capabilities": self.list_capabilities()["capabilities"],
            "package": self.package_info(),
            "network_health": self.network_health(),
            "system": self.system_info(),
        }

    def start_node_runtime(self) -> dict[str, Any]:
        """Prepare local runtime state before a foreground API/node process starts."""

        config = self.load_config() if self.paths.config_path.exists() else None
        identity_missing = (
            config is not None
            and _config_identity_persistence_enabled(config)
            and not _config_identity_path(config, self.paths.identity_path).exists()
        )
        if config is None or identity_missing:
            self.initialize_local_node_data()
        self.mark_runtime_started()
        status = self.get_node_status()
        self._append_event("node runtime started")
        return status

    def mark_runtime_started(self) -> None:
        self.paths.home.mkdir(parents=True, exist_ok=True)
        atomic_write_json(
            self.paths.pid_path,
            {"version": 1, "pid": os.getpid(), "started_at": int(time.time())},
        )

    def mark_runtime_stopped(self) -> None:
        try:
            self.paths.pid_path.unlink()
        except FileNotFoundError:
            pass
        self._append_event("node runtime stopped")

    def list_peers(self) -> dict[str, Any]:
        """Return known peers without inventing network state."""

        return {
            "bootstrap_status": "not_configured",
            "peer_count": 0,
            "peers": [],
            "note": "No peer discovery source is configured for the local daemon yet.",
        }

    def list_capabilities(self) -> dict[str, Any]:
        """Return the versioned local capability response used by ``/capabilities``.

        Response shape::

            {"schema_version": 1, "network_mode": "local-only-no-p2p",
             "capabilities": [{"identifier": str, "description": str,
                                "status": "enabled" | "disabled",
                                "schema_version": 1}], "advertised": False}

        Work entries are enabled from ``config.capabilities.enabled_work_types``;
        provenance entries come from the registered local artifact contracts.
        No entry represents remote discovery, consensus, or network advertising.
        """

        config = self.load_config()
        enabled_work_types = _config_enabled_work_types(config)
        capabilities = [
            {
                "identifier": identifier,
                "description": description,
                "status": "enabled" if work_type in enabled_work_types else "disabled",
                "schema_version": CAPABILITY_LIST_SCHEMA_VERSION,
                "work_type": work_type,
            }
            for identifier, description, work_type in LOCAL_CAPABILITY_DEFINITIONS
        ]
        capabilities.extend(
            {
                "identifier": identifier,
                "description": description,
                "status": (
                    "disabled"
                    if identifier == "provenance.creator_node_id"
                    and not _config_identity_persistence_enabled(config)
                    else status
                ),
                "schema_version": CAPABILITY_LIST_SCHEMA_VERSION,
            }
            for identifier, description, status in LOCAL_PROVENANCE_CAPABILITY_DEFINITIONS
        )
        return {
            "schema_version": CAPABILITY_LIST_SCHEMA_VERSION,
            "network_mode": "local-only-no-p2p",
            "capabilities": capabilities,
            "advertised": False,
            "note": "Capabilities are local-only registered definitions and are not advertised to a live network.",
        }

    def package_info(self) -> dict[str, Any]:
        """Return installed package metadata for launchers and local dashboards."""

        return {
            "name": "aethermesh",
            "version": _package_version(),
            "source": "installed",
        }

    def network_health(self) -> dict[str, Any]:
        """Return honest local-only network health for UI frontends."""

        config = self.load_config()
        peers = self.list_peers()
        host = _config_api_host(config)
        return {
            "status": "local_only",
            "peer_count": peers["peer_count"],
            "api_reachable": True,
            "localhost_only": host in {"127.0.0.1", "localhost"},
            "note": "Public peer networking is not configured for this local prototype.",
        }

    def list_jobs(self) -> dict[str, Any]:
        """Return local job buckets without faking work."""

        return {
            "current": [],
            "completed": [],
            "failed": [],
            "validation_status": "not_active",
            "note": "No persistent daemon job queue is active yet.",
        }

    def submit_local_job(self, request: dict[str, Any]) -> dict[str, Any]:
        """Accept one local job request without dispatching or validating it."""

        if not isinstance(request, dict):
            raise RuntimeServiceError("job submission must be a JSON object")
        creator_node_id = request.get("creator_node_id")
        if not isinstance(creator_node_id, str) or not creator_node_id.strip():
            raise RuntimeServiceError(
                "job submission creator_node_id must be a non-empty string"
            )
        job_type = request.get("job_type")
        if not isinstance(job_type, str) or not job_type.strip():
            raise RuntimeServiceError(
                "job submission job_type must be a non-empty string"
            )
        payload = request.get("payload")
        if not isinstance(payload, dict):
            raise RuntimeServiceError("job submission payload must be a JSON object")
        validation_mode = request.get("requested_validation_mode")
        if not isinstance(validation_mode, str) or not validation_mode.strip():
            raise RuntimeServiceError(
                "job submission requested_validation_mode must be a non-empty string"
            )
        lineage_parent_refs = request.get("lineage_parent_refs", [])
        if not isinstance(lineage_parent_refs, list) or not all(
            isinstance(ref, str) and ref.strip() for ref in lineage_parent_refs
        ):
            raise RuntimeServiceError(
                "job submission lineage_parent_refs must be a list of non-empty strings"
            )
        attribution_metadata = request.get("attribution_metadata", {})
        if not isinstance(attribution_metadata, dict):
            raise RuntimeServiceError(
                "job submission attribution_metadata must be a JSON object"
            )
        try:
            json.dumps(request, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise RuntimeServiceError(
                "job submission must contain JSON-compatible data"
            ) from exc

        job_id = f"local-job-{uuid4().hex}"
        manifest_path = self.paths.data_dir / "job-submissions" / f"{job_id}.json"
        manifest_ref = f"data/job-submissions/{job_id}.json"
        atomic_create_json(
            manifest_path,
            {
                "version": 1,
                "manifest_type": "local_job_submission",
                "network_mode": "local-only-no-p2p",
                "submitted_at": int(time.time()),
                "job": {"job_id": job_id, "job_type": job_type, "payload": payload},
                "creator_node_id": creator_node_id,
                "requested_validation_mode": validation_mode,
                "lineage": {"parent_refs": lineage_parent_refs},
                "contribution_attribution": {
                    "creator_node_id": creator_node_id,
                    "metadata": attribution_metadata,
                },
            },
        )
        self._append_event(f"accepted local job submission {job_id}")
        return {
            "job_id": job_id,
            "status": "accepted_pending_execution",
            "manifest_ref": manifest_ref,
            "next_validation_expectation": "pending_requested_local_validation",
            "network_mode": "local-only-no-p2p",
        }

    def get_local_job_status(self, job_id: str) -> dict[str, Any]:
        """Read one submission and its optional local execution evidence."""

        missing = {
            "job_id": job_id,
            "status": "not_found",
            "error": "local job not found",
        }
        if not self._is_local_job_id(job_id):
            return missing
        manifest_path = self.paths.data_dir / "job-submissions" / f"{job_id}.json"
        if not manifest_path.exists():
            return missing
        manifest = self._load_local_job_document(
            manifest_path, "job submission manifest"
        )
        if manifest.get("job", {}).get("job_id") != job_id:
            raise RuntimeServiceError(
                "job submission manifest job_id does not match its path"
            )
        status_path = self.paths.data_dir / "job-status" / f"{job_id}.json"
        status = (
            self._load_local_job_document(status_path, "job status record")
            if status_path.exists()
            else {}
        )
        return {
            "job_id": job_id,
            "status": status.get("status", "queued"),
            "manifest_ref": f"data/job-submissions/{job_id}.json",
            "creator_node_id": manifest["creator_node_id"],
            "worker_node_id": status.get("worker_node_id"),
            "lineage": manifest["lineage"],
            "contribution_attribution": status.get(
                "contribution_attribution", manifest["contribution_attribution"]
            ),
            "validation": status.get("validation"),
            "result": status.get("result"),
            "error": status.get("error"),
            "network_mode": "local-only-no-p2p",
        }

    def inspect_local_audit_events(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        start_time: int | None = None,
        end_time: int | None = None,
        node_id: str | None = None,
        event_type: str | None = None,
        manifest_id: str | None = None,
        receipt_id: str | None = None,
        lineage_id: str | None = None,
        contribution_attribution_id: str | None = None,
    ) -> dict[str, Any]:
        """Read derived local job audit events without mutating stored evidence."""
        filters = {
            "event_type": event_type,
            "node_id": node_id,
            "manifest_id": manifest_id,
            "receipt_id": receipt_id,
            "lineage_id": lineage_id,
            "contribution_attribution_id": contribution_attribution_id,
        }
        for name, value in filters.items():
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise RuntimeServiceError(f"{name} must be a non-empty string")
        for name, time_value in (("start_time", start_time), ("end_time", end_time)):
            if time_value is not None and (
                not isinstance(time_value, int) or isinstance(time_value, bool)
            ):
                raise RuntimeServiceError(f"{name} must be an integer Unix timestamp")
        if start_time is not None and end_time is not None and start_time > end_time:
            raise RuntimeServiceError("start_time must not be greater than end_time")
        if (
            not isinstance(limit, int)
            or isinstance(limit, bool)
            or not 1 <= limit <= 100
        ):
            raise RuntimeServiceError("limit must be an integer between 1 and 100")
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise RuntimeServiceError("offset must be a non-negative integer")
        if event_type is not None and event_type not in {
            "job_submitted",
            "job_executed",
        }:
            raise RuntimeServiceError(
                "event_type must be job_submitted or job_executed"
            )
        directory = self.paths.data_dir / "job-submissions"
        events = (
            [
                event
                for path in sorted(directory.glob("*.json"))
                for event in self._audit_events_for_manifest(path)
            ]
            if directory.exists()
            else []
        )

        def matches(event: dict[str, Any]) -> bool:
            artifacts = event["artifacts"]
            return (
                (start_time is None or event["timestamp"] >= start_time)
                and (end_time is None or event["timestamp"] <= end_time)
                and (event_type is None or event["event_type"] == event_type)
                and (
                    node_id is None
                    or node_id in {event["actor_node_id"], event["creator_node_id"]}
                )
                and (manifest_id is None or artifacts["manifest_id"] == manifest_id)
                and (receipt_id is None or artifacts["receipt_id"] == receipt_id)
                and (lineage_id is None or artifacts["lineage_id"] == lineage_id)
                and (
                    contribution_attribution_id is None
                    or artifacts["contribution_attribution_id"]
                    == contribution_attribution_id
                )
            )

        events = [event for event in events if matches(event)]
        events.sort(
            key=lambda event: (event["timestamp"], event["event_id"]), reverse=True
        )
        return {
            "schema_version": 1,
            "network_mode": "local-only-no-p2p",
            "query": {
                **filters,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit,
                "offset": offset,
            },
            "total_matching": len(events),
            "events": events[offset : offset + limit],
        }

    def _audit_events_for_manifest(self, manifest_path: Path) -> list[dict[str, Any]]:
        manifest = self._load_local_job_document(
            manifest_path, "job submission manifest"
        )
        job_id = manifest.get("job", {}).get("job_id")
        creator = manifest.get("creator_node_id")
        submitted_at = manifest.get("submitted_at")
        lineage = manifest.get("lineage")
        if (
            not self._is_local_job_id(job_id)
            or manifest_path.stem != job_id
            or not isinstance(creator, str)
            or not creator
            or not isinstance(submitted_at, int)
            or isinstance(submitted_at, bool)
            or not isinstance(lineage, dict)
            or not isinstance(lineage.get("parent_refs"), list)
        ):
            raise RuntimeServiceError(
                "job submission manifest has invalid audit evidence"
            )
        artifacts: dict[str, Any] = {
            "manifest_id": job_id,
            "manifest_ref": f"data/job-submissions/{job_id}.json",
            "receipt_id": None,
            "receipt_ref": None,
            "lineage_id": f"local-lineage-{job_id}",
            "lineage_parent_refs": list(lineage["parent_refs"]),
            "contribution_attribution_id": f"local-contribution-{job_id}",
        }
        events = [
            {
                "event_id": f"local-audit-{job_id}-submitted",
                "timestamp": submitted_at,
                "event_type": "job_submitted",
                "actor_node_id": creator,
                "creator_node_id": creator,
                "artifacts": artifacts,
                "validation_status": "pending",
            }
        ]
        status_path = self.paths.data_dir / "job-status" / f"{job_id}.json"
        if not status_path.exists():
            return events
        status = self._load_local_job_document(status_path, "job status record")
        validation = status.get("validation")
        receipt_ref = (
            validation.get("receipt_ref") if isinstance(validation, dict) else None
        )
        expected_receipt_ref = f"data/job-validation-receipts/{job_id}.json"
        worker = status.get("worker_node_id")
        if (
            status.get("job_id") != job_id
            or not isinstance(worker, str)
            or not worker
            or not isinstance(validation, dict)
            or receipt_ref != expected_receipt_ref
        ):
            raise RuntimeServiceError("job status has invalid audit evidence")
        receipt = self._load_local_job_document(
            self.paths.home / expected_receipt_ref, "validation receipt"
        )
        validated_at = receipt.get("validated_at")
        if (
            receipt.get("job_id") != job_id
            or receipt.get("receipt_id") != self._receipt_id_for_job(job_id)
            or not isinstance(validated_at, int)
            or isinstance(validated_at, bool)
        ):
            raise RuntimeServiceError("validation receipt has invalid audit evidence")
        events.append(
            {
                "event_id": f"local-audit-{job_id}-executed",
                "timestamp": validated_at,
                "event_type": "job_executed",
                "actor_node_id": worker,
                "creator_node_id": creator,
                "artifacts": {
                    **artifacts,
                    "receipt_id": receipt["receipt_id"],
                    "receipt_ref": receipt_ref,
                },
                "validation_status": "passed" if validation.get("passed") else "failed",
            }
        )
        return events

    def contribution_summary(self) -> dict[str, Any]:
        """Read local job evidence into a deterministic, non-mutating summary."""

        manifests = self.paths.data_dir / "job-submissions"
        statuses = self.paths.data_dir / "job-status"
        job_ids = sorted(
            {
                path.stem
                for directory in (manifests, statuses)
                if directory.exists()
                for path in directory.glob("*.json")
            }
        )
        items = [self._contribution_summary_item(job_id) for job_id in job_ids]
        accepted_work_count = sum(
            1 for item in items if item["acceptance_status"] == "accepted"
        )
        return {
            "network_mode": "local-only-no-p2p",
            "summary_status": "empty" if not items else "recorded",
            "accepted_work_count": accepted_work_count,
            "non_accepted_work_count": len(items) - accepted_work_count,
            "items": items,
        }

    def get_local_validation_receipt(
        self,
        *,
        receipt_id: str | None = None,
        work_id: str | None = None,
        latest: bool = False,
    ) -> dict[str, Any]:
        """Return one stored local receipt without creating validation evidence."""

        selectors = sum(value is not None for value in (receipt_id, work_id)) + int(
            latest
        )
        if selectors != 1:
            raise RuntimeServiceError(
                "exactly one of receipt_id, work_id, or latest is required"
            )
        if receipt_id is not None:
            job_id = self._job_id_from_receipt_id(receipt_id)
        elif work_id is not None:
            if not self._is_local_job_id(work_id):
                raise RuntimeServiceError("work_id must be a local job ID")
            job_id = work_id
        else:
            job_id = self._latest_validation_receipt_work_id()

        receipt_ref = f"data/job-validation-receipts/{job_id}.json"
        receipt_path = self.paths.home / receipt_ref
        if not receipt_path.exists():
            raise ValidationReceiptNotFoundError("local validation receipt not found")
        receipt = self._load_local_job_document(receipt_path, "validation receipt")
        result_ref = receipt.get("result_ref")
        validator_id = receipt.get("validator_id")
        validation = receipt.get("validation")
        if receipt.get("job_id") != job_id:
            raise RuntimeServiceError("validation receipt does not match its work ID")
        expected_result_ref = f"data/job-results/{job_id}.json"
        if result_ref != expected_result_ref:
            raise RuntimeServiceError(
                "validation receipt does not match its work result"
            )
        if not isinstance(validator_id, str) or not validator_id:
            raise RuntimeServiceError("validation receipt has no validator identity")
        if not isinstance(validation, dict) or not isinstance(
            validation.get("valid"), bool
        ):
            raise RuntimeServiceError(
                "validation receipt has invalid validation evidence"
            )

        manifest_ref = f"data/job-submissions/{job_id}.json"
        status_ref = f"data/job-status/{job_id}.json"
        manifest_path = self.paths.home / manifest_ref
        status_path = self.paths.home / status_ref
        if not manifest_path.exists() or not status_path.exists():
            raise RuntimeServiceError(
                "validation receipt has incomplete local evidence"
            )
        manifest = self._load_local_job_document(
            manifest_path, "job submission manifest"
        )
        status = self._load_local_job_document(status_path, "job status record")
        lineage = manifest.get("lineage")
        attribution = status.get("contribution_attribution")
        if (
            not isinstance(manifest.get("creator_node_id"), str)
            or manifest.get("job", {}).get("job_id") != job_id
            or status.get("job_id") != job_id
            or not isinstance(lineage, dict)
            or not isinstance(lineage.get("parent_refs"), list)
            or not isinstance(attribution, dict)
            or attribution.get("creator_node_id") != manifest.get("creator_node_id")
        ):
            raise RuntimeServiceError(
                "validation receipt has incomplete provenance evidence"
            )
        if status.get("validation", {}).get("receipt_ref") != receipt_ref:
            raise RuntimeServiceError(
                "job status does not reference validation receipt"
            )

        validated_at = receipt.get("validated_at")
        timestamp_source = "receipt_record"
        if not isinstance(validated_at, int) or isinstance(validated_at, bool):
            validated_at = int(receipt_path.stat().st_mtime)
            timestamp_source = "receipt_file_mtime_legacy"
        return {
            "schema_version": 1,
            "network_mode": "local-only-no-p2p",
            "validation_scope": "local-only-not-consensus",
            "receipt_id": self._receipt_id_for_job(job_id),
            "work_id": job_id,
            "creator_node_id": manifest["creator_node_id"],
            "manifest_ref": manifest_ref,
            "validation_status": "passed" if validation["valid"] else "failed",
            "validation": validation,
            "validation_timestamp": validated_at,
            "validation_timestamp_source": timestamp_source,
            "validator_identity": validator_id,
            "lineage_parent_ids": lineage["parent_refs"],
            "contribution_attribution": attribution,
            "evidence": {
                "receipt_ref": receipt_ref,
                "result_ref": result_ref,
                "status_ref": status_ref,
            },
        }

    @staticmethod
    def _receipt_id_for_job(job_id: str) -> str:
        return f"{VALIDATION_RECEIPT_ID_PREFIX}{job_id}"

    def _job_id_from_receipt_id(self, receipt_id: str) -> str:
        if not isinstance(receipt_id, str) or not receipt_id.startswith(
            VALIDATION_RECEIPT_ID_PREFIX
        ):
            raise RuntimeServiceError(
                "receipt_id must be a local validation receipt ID"
            )
        job_id = receipt_id.removeprefix(VALIDATION_RECEIPT_ID_PREFIX)
        if not self._is_local_job_id(job_id):
            raise RuntimeServiceError(
                "receipt_id must be a local validation receipt ID"
            )
        return job_id

    def _latest_validation_receipt_work_id(self) -> str:
        directory = self.paths.data_dir / "job-validation-receipts"
        candidates = (
            [
                path
                for path in directory.glob("*.json")
                if self._is_local_job_id(path.stem)
            ]
            if directory.exists()
            else []
        )
        if not candidates:
            raise ValidationReceiptNotFoundError("local validation receipt not found")
        return max(
            candidates, key=lambda path: (path.stat().st_mtime_ns, path.name)
        ).stem

    def _contribution_summary_item(self, job_id: str) -> dict[str, Any]:
        manifest_ref = f"data/job-submissions/{job_id}.json"
        status_ref = f"data/job-status/{job_id}.json"
        expected_receipt_ref = f"data/job-validation-receipts/{job_id}.json"
        manifest_path = self.paths.data_dir / "job-submissions" / f"{job_id}.json"
        status_path = self.paths.data_dir / "job-status" / f"{job_id}.json"
        evidence_errors: list[str] = []
        manifest = self._load_summary_document(
            manifest_path, "job submission manifest", evidence_errors
        )
        status = (
            self._load_summary_document(
                status_path, "job status record", evidence_errors
            )
            if status_path.exists()
            else {}
        )
        status_validation = status.get("validation")
        validation = status_validation if isinstance(status_validation, dict) else {}
        receipt_ref = validation.get("receipt_ref")
        receipt = {}
        if isinstance(receipt_ref, str) and receipt_ref:
            if receipt_ref != expected_receipt_ref:
                evidence_errors.append(
                    "validation receipt reference does not match work item"
                )
            else:
                receipt = self._load_summary_document(
                    self.paths.home / receipt_ref,
                    "validation receipt",
                    evidence_errors,
                )
        elif status:
            evidence_errors.append(
                "job status record has no validation receipt reference"
            )

        receipt_passed = (
            isinstance(receipt.get("validation"), dict)
            and receipt["validation"].get("valid") is True
        )
        manifest_job = manifest.get("job")
        if manifest:
            if not isinstance(manifest_job, dict):
                evidence_errors.append(
                    "job submission manifest has invalid job evidence"
                )
            elif manifest_job.get("job_id") != job_id:
                evidence_errors.append(
                    "job submission manifest does not match work item"
                )
        if status and status.get("job_id") != job_id:
            evidence_errors.append("job status record does not match work item")
        if receipt and receipt.get("job_id") != job_id:
            evidence_errors.append("validation receipt does not match work item")
        expected_result_ref = f"data/job-results/{job_id}.json"
        if receipt and receipt.get("result_ref") != expected_result_ref:
            evidence_errors.append("validation receipt does not match work result")
        accepted = (
            not evidence_errors
            and status.get("status") == "succeeded"
            and validation.get("passed") is True
            and receipt_passed
        )
        attribution = status.get("contribution_attribution")
        if not isinstance(attribution, dict):
            manifest_attribution = manifest.get("contribution_attribution")
            attribution = (
                manifest_attribution if isinstance(manifest_attribution, dict) else {}
            )
        creator_node_id = attribution.get("creator_node_id")
        contributing_node_id = attribution.get(
            "worker_node_id", status.get("worker_node_id")
        )
        if manifest and not isinstance(creator_node_id, str):
            evidence_errors.append("contribution attribution has no creator node ID")
        elif manifest and creator_node_id != manifest.get("creator_node_id"):
            evidence_errors.append(
                "contribution attribution creator does not match manifest"
            )
        if status.get("status") == "succeeded" and not isinstance(
            contributing_node_id, str
        ):
            evidence_errors.append(
                "contribution attribution has no contributing node ID"
            )
        elif status and contributing_node_id != status.get("worker_node_id"):
            evidence_errors.append(
                "contribution attribution worker does not match job status"
            )
        if receipt and receipt.get("validator_id") != status.get("worker_node_id"):
            evidence_errors.append("validation receipt validator does not match worker")
        lineage = manifest.get("lineage")
        if not isinstance(lineage, dict):
            lineage = {}
            if manifest:
                evidence_errors.append(
                    "job submission manifest has invalid lineage evidence"
                )
        lineage_links = lineage.get("parent_refs", [])
        if not isinstance(lineage_links, list):
            evidence_errors.append("job submission manifest has invalid lineage links")
            lineage_links = []
        accepted = accepted and not evidence_errors
        return {
            "work_item_id": job_id,
            "status": status.get("status", "incomplete"),
            "acceptance_status": "accepted"
            if accepted
            else "degraded"
            if evidence_errors
            else "not_accepted",
            "creator_node_id": creator_node_id,
            "contributing_node_id": contributing_node_id,
            "manifest_ref": manifest_ref,
            "status_ref": status_ref if status_path.exists() else None,
            "validation_receipt_ref": receipt_ref
            if isinstance(receipt_ref, str)
            else None,
            "lineage_links": lineage_links,
            "timestamps": {"submitted_at": manifest.get("submitted_at")},
            "evidence_errors": evidence_errors,
        }

    @staticmethod
    def _load_summary_document(
        path: Path, label: str, evidence_errors: list[str]
    ) -> dict[str, Any]:
        if not path.exists():
            evidence_errors.append(f"missing {label}: {path.name}")
            return {}
        try:
            return NodeRuntimeService._load_local_job_document(path, label)
        except RuntimeServiceError as exc:
            evidence_errors.append(str(exc))
            return {}

    def execute_submitted_local_job(
        self, job_id: str, worker_node_id: str
    ) -> dict[str, Any]:
        """Run a queued local submission; this is not a daemon or remote boundary."""

        before = self.get_local_job_status(job_id)
        if before["status"] == "not_found":
            raise RuntimeServiceError("local job not found")
        if before["status"] != "queued":
            raise RuntimeServiceError("local job is not queued")
        if not isinstance(worker_node_id, str) or not worker_node_id.strip():
            raise RuntimeServiceError("worker_node_id must be a non-empty string")
        manifest = self._load_local_job_document(
            self.paths.data_dir / "job-submissions" / f"{job_id}.json",
            "job submission manifest",
        )
        job_data = manifest["job"]
        job = Job(
            job_id=job_id, job_type=job_data["job_type"], payload=job_data["payload"]
        )
        result = LocalRunner(NodeIdentity(node_id=worker_node_id)).run(job)
        validation = validate_job_result(job, result)
        result_ref = f"data/job-results/{job_id}.json"
        receipt_ref = f"data/job-validation-receipts/{job_id}.json"
        atomic_create_json(
            self.paths.data_dir / "job-results" / f"{job_id}.json",
            {
                "version": 1,
                "job_id": job_id,
                "worker_node_id": worker_node_id,
                "result": result.to_dict(),
            },
        )
        atomic_create_json(
            self.paths.data_dir / "job-validation-receipts" / f"{job_id}.json",
            {
                "version": 1,
                "job_id": job_id,
                "receipt_id": self._receipt_id_for_job(job_id),
                "result_ref": result_ref,
                "validator_id": worker_node_id,
                "validation": validation.to_dict(),
                "validated_at": int(time.time()),
            },
        )
        succeeded = result.status == "completed" and validation.valid
        atomic_create_json(
            self.paths.data_dir / "job-status" / f"{job_id}.json",
            {
                "version": 1,
                "job_id": job_id,
                "status": "succeeded" if succeeded else "failed",
                "worker_node_id": worker_node_id,
                "result": {
                    "ref": result_ref,
                    "summary": result.output if succeeded else None,
                },
                "validation": {
                    "receipt_ref": receipt_ref,
                    "passed": validation.valid,
                    "reason": validation.reason,
                },
                "contribution_attribution": {
                    **manifest["contribution_attribution"],
                    "worker_node_id": worker_node_id,
                    "validated_contribution_units": result.contribution_units
                    if succeeded
                    else 0,
                },
                "error": result.error
                or (None if succeeded else f"validation failed: {validation.reason}"),
            },
        )
        self._append_event(f"executed local job submission {job_id}")
        return self.get_local_job_status(job_id)

    @staticmethod
    def _is_local_job_id(job_id: object) -> bool:
        prefix = "local-job-"
        suffix = job_id[len(prefix) :] if isinstance(job_id, str) else ""
        return (
            isinstance(job_id, str)
            and job_id.startswith(prefix)
            and len(suffix) == 32
            and all(character in "0123456789abcdef" for character in suffix)
        )

    @staticmethod
    def _load_local_job_document(path: Path, label: str) -> dict[str, Any]:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeServiceError(f"{label} JSON is malformed: {exc.msg}") from exc
        except OSError as exc:
            raise RuntimeServiceError(f"could not read {label}: {exc}") from exc
        if not isinstance(document, dict):
            raise RuntimeServiceError(f"{label} JSON must be an object")
        return document

    def health(self) -> dict[str, Any]:
        config = self.load_config()
        return {
            "ok": True,
            "service": "aethermesh-local-node",
            "version": _package_version(),
            "status": self.get_node_status()["status"],
            "bind_host": _config_api_host(config),
            "port": _config_api_port(config),
            "config_path": str(self.paths.config_path),
        }

    def recent_logs(self, limit: int = 100) -> dict[str, Any]:
        if not self.paths.events_path.exists():
            return {"events": []}
        lines = self.paths.events_path.read_text(encoding="utf-8").splitlines()
        return {"events": lines[-limit:]}

    def system_info(self) -> dict[str, Any]:
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        disk = shutil.disk_usage(self.paths.data_dir)
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "processor": platform.processor() or platform.machine(),
            "memory_total_bytes": _memory_total_bytes(),
            "disk_data_path_total_bytes": disk.total,
            "disk_data_path_free_bytes": disk.free,
        }

    def _default_config(
        self, node_id: str | None, node_name: str | None = None
    ) -> dict[str, Any]:
        return {
            "version": CONFIG_SCHEMA_VERSION,
            "node": {
                "node_id": node_id,
                "node_name": node_name,
                "status": "local_only",
            },
            "paths": {
                "home": str(self.paths.home),
                "data_dir": str(self.paths.data_dir),
                "log_dir": str(self.paths.log_dir),
            },
            "api": {"host": DEFAULT_API_HOST, "port": DEFAULT_API_PORT},
            "identity": {"persist": False, "path": str(self.paths.identity_path)},
            "capabilities": {"enabled_work_types": list(DEFAULT_LOCAL_CAPABILITIES)},
        }

    def _write_config(self, document: dict[str, Any]) -> None:
        try:
            atomic_write_json(self.paths.config_path, document)
        except OSError as exc:
            raise RuntimeServiceError(f"could not write config file: {exc}") from exc

    def _runtime_marker(self) -> tuple[bool, int | None, int | None]:
        if not self.paths.pid_path.exists():
            return False, None, None
        try:
            with self.paths.pid_path.open("r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (json.JSONDecodeError, OSError):
            return False, None, None
        pid = document.get("pid")
        started_at = document.get("started_at")
        if not isinstance(pid, int) or isinstance(pid, bool):
            return False, None, None
        if not _pid_is_alive(pid):
            return False, pid, None
        return True, pid, started_at if isinstance(started_at, int) else None

    def _append_event(self, message: str) -> None:
        self.paths.log_dir.mkdir(parents=True, exist_ok=True)
        line = f"{int(time.time())} {message}\n"
        with self.paths.events_path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def _default_home() -> Path:
    override = os.environ.get("AETHERMESH_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".aethermesh"


def _merge_config(existing: dict[str, Any], default: dict[str, Any]) -> dict[str, Any]:
    merged = dict(default)
    for key, value in existing.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def _config_node_id(config: dict[str, Any]) -> str | None:
    node = config.get("node")
    if not isinstance(node, dict):
        return None
    node_id = node.get("node_id")
    return node_id if isinstance(node_id, str) and node_id else None


def _config_enabled_work_types(config: dict[str, Any]) -> set[str]:
    capabilities = config.get("capabilities")
    if capabilities is None:
        return set(DEFAULT_LOCAL_CAPABILITIES)
    if not isinstance(capabilities, dict):
        raise RuntimeServiceError("config JSON field 'capabilities' must be an object")
    value = capabilities.get("enabled_work_types", list(DEFAULT_LOCAL_CAPABILITIES))
    if not isinstance(value, list) or not all(
        isinstance(work_type, str) and work_type for work_type in value
    ):
        raise RuntimeServiceError(
            "config JSON field 'capabilities.enabled_work_types' must be a list of non-empty strings"
        )
    return set(value)


def _config_identity_persistence_enabled(config: dict[str, Any]) -> bool:
    identity = config.get("identity")
    if identity is None:
        return False
    if not isinstance(identity, dict):
        raise RuntimeServiceError("config JSON field 'identity' must be an object")
    persist = identity.get("persist", False)
    if not isinstance(persist, bool):
        raise RuntimeServiceError(
            "config JSON field 'identity.persist' must be a boolean"
        )
    return persist


def _config_identity_path(config: dict[str, Any], default_path: Path) -> Path:
    identity = config.get("identity")
    if not isinstance(identity, dict):
        return default_path
    configured_path = identity.get("path")
    if configured_path is None:
        return default_path
    if not isinstance(configured_path, str) or not configured_path.strip():
        raise RuntimeServiceError(
            "config JSON field 'identity.path' must be a non-empty string"
        )
    path = Path(configured_path).expanduser()
    return path if path.is_absolute() else default_path.parent / path


def _config_node_name(config: dict[str, Any]) -> str | None:
    node = config.get("node")
    if not isinstance(node, dict):
        return None
    node_name = node.get("node_name")
    return node_name if isinstance(node_name, str) and node_name else None


def _config_api_host(config: dict[str, Any]) -> str:
    api = config.get("api")
    host = api.get("host") if isinstance(api, dict) else None
    if isinstance(host, str):
        return host
    return DEFAULT_API_HOST


def _config_api_port(config: dict[str, Any]) -> int:
    api = config.get("api")
    port = api.get("port") if isinstance(api, dict) else None
    if isinstance(port, int) and not isinstance(port, bool):
        return port
    return DEFAULT_API_PORT


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _package_version() -> str:
    return PUBLIC_VERSION


def _memory_total_bytes() -> int | None:
    if hasattr(os, "sysconf"):
        names = os.sysconf_names
        if "SC_PAGE_SIZE" in names and "SC_PHYS_PAGES" in names:
            try:
                return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
            except (OSError, ValueError):
                return None
    return None
