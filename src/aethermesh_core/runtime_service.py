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
from importlib import metadata
from pathlib import Path
from typing import Any

from aethermesh_core.identity import load_or_create_identity
from aethermesh_core.json_io import atomic_write_json

CONFIG_SCHEMA_VERSION = 1
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 7280


class RuntimeServiceError(ValueError):
    """Raised when local runtime state cannot be safely loaded or written."""


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
        identity = load_or_create_identity(self.paths.identity_path)
        config = self._default_config(node_id=identity.node_id)
        if self.paths.config_path.exists():
            existing = self.load_config()
            config = _merge_config(existing, config)
            config.setdefault("node", {})["node_id"] = identity.node_id
        self._write_config(config)
        if not self.paths.events_path.exists():
            self.paths.events_path.write_text("", encoding="utf-8")
        self._append_event("initialized local node data")
        return {
            "initialized": True,
            "node_id": identity.node_id,
            "home": str(self.paths.home),
            "config_path": str(self.paths.config_path),
            "data_dir": str(self.paths.data_dir),
            "log_dir": str(self.paths.log_dir),
            "identity_path": str(self.paths.identity_path),
        }

    def get_node_status(self) -> dict[str, Any]:
        """Return an honest local node status snapshot."""

        config = self.load_config()
        node_id = _config_node_id(config)
        running, pid, started_at = self._runtime_marker()
        uptime_seconds: int | None = None
        if running and started_at is not None:
            uptime_seconds = max(0, int(time.time() - started_at))
        jobs = self.list_jobs()
        peers = self.list_peers()
        return {
            "initialized": self.paths.config_path.exists()
            and self.paths.identity_path.exists(),
            "node_id": node_id,
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
            "system": self.system_info(),
        }

    def start_node_runtime(self) -> dict[str, Any]:
        """Prepare local runtime state before a foreground API/node process starts."""

        if not self.paths.config_path.exists() or not self.paths.identity_path.exists():
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

    def list_jobs(self) -> dict[str, Any]:
        """Return local job buckets without faking work."""

        return {
            "current": [],
            "completed": [],
            "failed": [],
            "validation_status": "not_active",
            "note": "No persistent daemon job queue is active yet.",
        }

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

    def _default_config(self, node_id: str | None) -> dict[str, Any]:
        return {
            "version": CONFIG_SCHEMA_VERSION,
            "node": {"node_id": node_id, "status": "local_only"},
            "paths": {
                "home": str(self.paths.home),
                "data_dir": str(self.paths.data_dir),
                "log_dir": str(self.paths.log_dir),
            },
            "api": {"host": DEFAULT_API_HOST, "port": DEFAULT_API_PORT},
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
    for package_name in ("aethermesh", "aethermesh-core"):
        try:
            return metadata.version(package_name)
        except metadata.PackageNotFoundError:
            continue
    return "0.1.0"


def _memory_total_bytes() -> int | None:
    if hasattr(os, "sysconf"):
        names = os.sysconf_names
        if "SC_PAGE_SIZE" in names and "SC_PHYS_PAGES" in names:
            try:
                return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
            except (OSError, ValueError):
                return None
    return None
