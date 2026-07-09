import asyncio
import builtins
import json
import os
import subprocess
import sys
import tempfile
import time
import types
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from typer.testing import CliRunner

from aethermesh_core import app_cli
from aethermesh_core.api import _lifespan, create_app
from aethermesh_core.release_update import ReleaseUpdateError
from aethermesh_core.runtime_service import (
    NodeRuntimeService,
    RuntimeServiceError,
    _config_api_host,
    _config_api_port,
    _config_identity_path,
    _config_identity_persistence_enabled,
    _config_node_id,
    _config_node_name,
    _default_home,
    _memory_total_bytes,
    _merge_config,
    _package_version,
    _pid_is_alive,
)


async def _fetch_api_payloads(api_app: FastAPI) -> dict[str, Any]:
    transport = httpx.ASGITransport(app=api_app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return {
            "health": (await client.get("/health")).json(),
            "status": (await client.get("/api/status")).json(),
            "status_alias": (await client.get("/status")).json(),
            "version_alias": (await client.get("/version")).json(),
            "node": (await client.get("/api/node")).json(),
            "node_alias": (await client.get("/node")).json(),
            "peers": (await client.get("/api/peers")).json(),
            "peers_alias": (await client.get("/peers")).json(),
            "jobs": (await client.get("/api/jobs")).json(),
            "capabilities": (await client.get("/api/capabilities")).json(),
            "capabilities_alias": (await client.get("/capabilities")).json(),
            "package": (await client.get("/api/package")).json(),
            "network": (await client.get("/api/network")).json(),
            "logs": (await client.get("/api/logs")).json(),
            "logs_alias": (await client.get("/logs")).json(),
            "events": (await client.get("/api/events")).json(),
            "shutdown": (await client.post("/shutdown")).json(),
            "restart": (await client.post("/restart")).json(),
            "html": (await client.get("/")).text,
        }


class RuntimeServiceTests(unittest.TestCase):
    def test_init_creates_reusable_local_node_data_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))

            initialized = service.initialize_local_node_data()
            status = service.get_node_status()

            self.assertEqual(
                set(initialized),
                {
                    "initialized",
                    "node_id",
                    "node_name",
                    "home",
                    "config_path",
                    "data_dir",
                    "log_dir",
                    "identity_path",
                    "identity_persisted",
                },
            )
            self.assertTrue(initialized["initialized"])
            self.assertEqual(initialized["home"], str(Path(temp_dir)))
            self.assertEqual(
                initialized["config_path"], str(Path(temp_dir) / "config.json")
            )
            self.assertEqual(initialized["data_dir"], str(Path(temp_dir) / "data"))
            self.assertEqual(initialized["log_dir"], str(Path(temp_dir) / "logs"))
            self.assertEqual(
                initialized["identity_path"], str(Path(temp_dir) / "identity.json")
            )
            self.assertFalse(initialized["identity_persisted"])
            self.assertFalse(Path(initialized["identity_path"]).exists())
            self.assertEqual(
                service.recent_logs(limit=1)["events"][0].split(" ", 1)[1],
                "initialized local node data",
            )
            self.assertEqual(
                set(status),
                {
                    "initialized",
                    "node_id",
                    "node_name",
                    "status",
                    "version",
                    "uptime_seconds",
                    "pid",
                    "config_path",
                    "data_dir",
                    "log_dir",
                    "api",
                    "peer_count",
                    "job_counts",
                    "capabilities",
                    "package",
                    "network_health",
                    "system",
                },
            )
            self.assertTrue(status["initialized"])
            self.assertRegex(
                str(status["node_name"]),
                r"^[a-z]+-[a-z]+-[a-z]+-[a-z]+_[a-f0-9]{6}$",
            )
            self.assertEqual(initialized["node_name"], status["node_name"])
            self.assertEqual(
                str(status["node_name"]).rsplit("_", 1)[1], status["node_id"][:6]
            )
            self.assertEqual(status["status"], "stopped")
            self.assertIsNone(status["uptime_seconds"])
            self.assertIsNone(status["pid"])
            self.assertEqual(status["api"]["host"], "127.0.0.1")
            self.assertEqual(status["api"]["port"], 7280)
            self.assertTrue(status["api"]["localhost_only"])
            self.assertEqual(status["peer_count"], 0)
            self.assertEqual(
                status["job_counts"], {"current": 0, "completed": 0, "failed": 0}
            )
            self.assertEqual(
                set(status["system"]),
                {
                    "platform",
                    "python_version",
                    "cpu_count",
                    "processor",
                    "memory_total_bytes",
                    "disk_data_path_total_bytes",
                    "disk_data_path_free_bytes",
                },
            )

            config = json.loads((Path(temp_dir) / "config.json").read_text())
            self.assertEqual(config["version"], 1)
            self.assertEqual(config["node"]["node_id"], status["node_id"])
            self.assertEqual(config["node"]["node_name"], status["node_name"])
            self.assertEqual(config["node"]["status"], "local_only")
            self.assertEqual(config["paths"]["home"], str(Path(temp_dir)))
            self.assertEqual(config["paths"]["data_dir"], str(Path(temp_dir) / "data"))
            self.assertEqual(config["paths"]["log_dir"], str(Path(temp_dir) / "logs"))
            self.assertEqual(config["api"], {"host": "127.0.0.1", "port": 7280})
            self.assertEqual(
                config["identity"],
                {"persist": False, "path": str(Path(temp_dir) / "identity.json")},
            )

            with patch.object(
                service, "_runtime_marker", return_value=(False, None, int(time.time()))
            ):
                self.assertIsNone(service.get_node_status()["uptime_seconds"])

    def test_identity_persistence_only_when_configured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            service.paths.home.mkdir(parents=True, exist_ok=True)
            persistent_config = service._default_config(node_id=None)
            persistent_config["identity"] = {
                "persist": True,
                "path": "identity.json",
            }
            service._write_config(persistent_config)

            first = service.initialize_local_node_data()
            persisted_document = json.loads(service.paths.identity_path.read_text())
            second = service.initialize_local_node_data()

            self.assertTrue(first["identity_persisted"])
            self.assertTrue(service.paths.identity_path.exists())
            self.assertEqual(first["identity_path"], str(service.paths.identity_path))
            self.assertEqual(first["node_id"], second["node_id"])
            self.assertEqual(
                persisted_document["node"]["creator_node_id"], first["node_id"]
            )
            self.assertEqual(persisted_document["references"]["manifest_refs"], [])
            self.assertEqual(
                persisted_document["references"]["validation_receipt_refs"], []
            )
            self.assertIn("version_metadata", persisted_document["references"])
            self.assertEqual(
                persisted_document["lineage"],
                {"parent_node_ids": [], "lineage_links": []},
            )
            self.assertEqual(
                persisted_document["contribution_attribution"],
                {
                    "creator_node_id": first["node_id"],
                    "attribution_node_id": first["node_id"],
                    "contribution_refs": [],
                },
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            first = service.initialize_local_node_data()
            second = service.initialize_local_node_data()

            self.assertFalse(first["identity_persisted"])
            self.assertFalse(service.paths.identity_path.exists())
            self.assertEqual(first["node_id"], second["node_id"])

    def test_persisted_identity_manifest_survives_restart_without_rewrite(self) -> None:
        first_node_id = "a" * 64
        fresh_node_id = "b" * 64
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "persisted-node"
            service = NodeRuntimeService.from_home(home)
            service.paths.home.mkdir(parents=True, exist_ok=True)
            persistent_config = service._default_config(node_id=None)
            persistent_config["identity"] = {"persist": True, "path": "identity.json"}
            service._write_config(persistent_config)

            with patch(
                "aethermesh_core.identity._new_local_node_id",
                return_value=first_node_id,
            ):
                first = service.initialize_local_node_data()
                service.mark_runtime_started()
            persisted_document = json.loads(service.paths.identity_path.read_text())
            persisted_document["references"]["manifest_refs"] = [
                f"manifests/local-batch.json#node:{first_node_id}"
            ]
            persisted_document["references"]["validation_receipt_refs"] = [
                "receipts/validation-0001.json"
            ]
            persisted_document["lineage"]["parent_node_ids"] = ["local-root"]
            persisted_document["lineage"]["lineage_links"] = [
                "lineage/local-node-link.json"
            ]
            persisted_document["contribution_attribution"]["contribution_refs"] = [
                "contributions/contribution-0001.json"
            ]
            service.paths.identity_path.write_text(
                json.dumps(persisted_document), encoding="utf-8"
            )
            manifest_after_first_start = json.loads(
                service.paths.identity_path.read_text(encoding="utf-8")
            )
            service.mark_runtime_stopped()

            restarted_service = NodeRuntimeService.from_home(home)
            with patch(
                "aethermesh_core.identity._new_local_node_id",
                side_effect=AssertionError("restart must reuse persisted identity"),
            ):
                restarted = restarted_service.initialize_local_node_data()
                restarted_status = restarted_service.start_node_runtime()
            manifest_after_restart = json.loads(
                restarted_service.paths.identity_path.read_text(encoding="utf-8")
            )
            restarted_service.mark_runtime_stopped()

            fresh_home = Path(temp_dir) / "fresh-node"
            fresh_service = NodeRuntimeService.from_home(fresh_home)
            fresh_service.paths.home.mkdir(parents=True, exist_ok=True)
            fresh_config = fresh_service._default_config(node_id=None)
            fresh_config["identity"] = {"persist": True, "path": "identity.json"}
            fresh_service._write_config(fresh_config)
            with patch(
                "aethermesh_core.identity._new_local_node_id",
                return_value=fresh_node_id,
            ):
                fresh = fresh_service.initialize_local_node_data()
            fresh_manifest = json.loads(
                fresh_service.paths.identity_path.read_text(encoding="utf-8")
            )

        self.assertEqual(first["node_id"], first_node_id)
        self.assertEqual(restarted["node_id"], first_node_id)
        self.assertEqual(restarted_status["node_id"], first_node_id)
        self.assertEqual(manifest_after_restart, manifest_after_first_start)
        self.assertEqual(
            manifest_after_restart["node"]["creator_node_id"], first_node_id
        )
        self.assertEqual(
            manifest_after_restart["contribution_attribution"]["creator_node_id"],
            first_node_id,
        )
        self.assertEqual(
            manifest_after_restart["contribution_attribution"]["attribution_node_id"],
            first_node_id,
        )
        self.assertEqual(
            manifest_after_restart["references"]["manifest_refs"],
            [f"manifests/local-batch.json#node:{first_node_id}"],
        )
        self.assertEqual(
            manifest_after_restart["references"]["validation_receipt_refs"],
            ["receipts/validation-0001.json"],
        )
        self.assertEqual(
            manifest_after_restart["lineage"],
            {
                "parent_node_ids": ["local-root"],
                "lineage_links": ["lineage/local-node-link.json"],
            },
        )
        self.assertEqual(
            manifest_after_restart["contribution_attribution"]["contribution_refs"],
            ["contributions/contribution-0001.json"],
        )
        self.assertEqual(fresh["node_id"], fresh_node_id)
        self.assertNotEqual(fresh["node_id"], first["node_id"])
        self.assertEqual(fresh_manifest["node"]["creator_node_id"], fresh_node_id)

    def test_peers_jobs_and_health_are_honest_when_node_has_no_runtime_work(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            service.initialize_local_node_data()

            self.assertEqual(
                service.list_peers(),
                {
                    "bootstrap_status": "not_configured",
                    "peer_count": 0,
                    "peers": [],
                    "note": "No peer discovery source is configured for the local daemon yet.",
                },
            )
            self.assertEqual(
                service.list_capabilities(),
                {
                    "capabilities": [
                        "echo",
                        "keyword_extract",
                        "text_chunk",
                        "text_embed",
                        "text_stats",
                    ],
                    "advertised": False,
                    "note": "Local prototype capabilities are available but not advertised to a live network yet.",
                },
            )
            self.assertEqual(
                service.network_health(),
                {
                    "status": "local_only",
                    "peer_count": 0,
                    "api_reachable": True,
                    "localhost_only": True,
                    "note": "Public peer networking is not configured for this local prototype.",
                },
            )
            package = service.package_info()
            self.assertEqual(package["name"], "aethermesh")
            self.assertIn("version", package)
            self.assertEqual(package["source"], "installed")
            self.assertEqual(
                service.list_jobs(),
                {
                    "current": [],
                    "completed": [],
                    "failed": [],
                    "validation_status": "not_active",
                    "note": "No persistent daemon job queue is active yet.",
                },
            )
            self.assertEqual(service.health()["ok"], True)
            self.assertEqual(service.health()["bind_host"], "127.0.0.1")

    def test_existing_config_is_merged_and_logs_are_limited(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            service.paths.home.mkdir(parents=True, exist_ok=True)
            service.paths.log_dir.mkdir(parents=True)
            service.paths.config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "node": {"node_id": "stale-node", "label": "dev"},
                        "api": {"host": "localhost", "port": 9999},
                        "custom": "kept",
                    }
                ),
                encoding="utf-8",
            )
            service.paths.events_path.write_text("one\ntwo\n", encoding="utf-8")

            result = service.initialize_local_node_data()

            config = service.load_config()
            self.assertEqual(config["custom"], "kept")
            self.assertEqual(config["node"]["label"], "dev")
            self.assertEqual(config["node"]["node_id"], result["node_id"])
            self.assertEqual(config["node"]["node_name"], result["node_name"])
            self.assertEqual(config["api"], {"host": "localhost", "port": 9999})
            self.assertEqual(len(service.recent_logs(limit=2)["events"]), 2)

            service.paths.events_path.write_text(
                "\n".join(f"event-{index}" for index in range(101)) + "\n",
                encoding="utf-8",
            )
            default_logs = service.recent_logs()["events"]
            self.assertEqual(len(default_logs), 100)
            self.assertEqual(default_logs[0], "event-1")
            self.assertEqual(default_logs[-1], "event-100")

    def test_runtime_markers_cover_started_stopped_and_bad_marker_states(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))

            status = service.start_node_runtime()
            self.assertEqual(status["status"], "running")
            self.assertIsInstance(status["uptime_seconds"], int)
            self.assertTrue(service.paths.pid_path.exists())
            restarted = service.start_node_runtime()
            self.assertEqual(restarted["status"], "running")

            service.mark_runtime_stopped()
            self.assertFalse(service.paths.pid_path.exists())
            service.mark_runtime_stopped()

            service.paths.pid_path.write_text("not json", encoding="utf-8")
            self.assertEqual(service._runtime_marker(), (False, None, None))
            service.paths.pid_path.write_text(
                json.dumps({"version": 1, "pid": True}), encoding="utf-8"
            )
            self.assertEqual(service._runtime_marker(), (False, None, None))
            service.paths.pid_path.write_text(
                json.dumps({"version": 1, "pid": 999999999}), encoding="utf-8"
            )
            self.assertEqual(service._runtime_marker(), (False, 999999999, None))

        with tempfile.TemporaryDirectory() as temp_dir:
            nested_home = Path(temp_dir) / "nested" / "runtime"
            service = NodeRuntimeService.from_home(nested_home)
            initialized = service.initialize_local_node_data()
            self.assertEqual(initialized["home"], str(nested_home))
            self.assertTrue(service.paths.config_path.exists())
            self.assertFalse(service.paths.identity_path.exists())

        with tempfile.TemporaryDirectory() as temp_dir:
            nested_home = Path(temp_dir) / "nested" / "runtime"
            service = NodeRuntimeService.from_home(nested_home)
            service.mark_runtime_started()
            self.assertTrue(service.paths.pid_path.exists())

        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            service.paths.home.mkdir(parents=True, exist_ok=True)
            service._write_config(service._default_config(node_id="orphaned-config"))
            self.assertFalse(service.paths.identity_path.exists())
            status = service.start_node_runtime()
            self.assertEqual(status["status"], "running")
            self.assertFalse(service.paths.identity_path.exists())

    def test_config_errors_and_defaults_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            self.assertEqual(service.recent_logs(), {"events": []})
            service.paths.home.mkdir(parents=True, exist_ok=True)
            service.paths.config_path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeServiceError, "config JSON must be an object"
            ):
                service.load_config()
            service.paths.config_path.write_text(
                json.dumps({"version": 2}), encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeServiceError, "version 1"):
                service.load_config()

        self.assertIsNone(_config_node_id({"node": []}))
        self.assertEqual(_config_node_id({"node": {"node_id": "node-a"}}), "node-a")
        self.assertIsNone(_config_node_id({"node": {"node_id": ""}}))
        self.assertIsNone(_config_node_name({"node": []}))
        self.assertEqual(
            _config_node_name(
                {"node": {"node_name": "lucid-beacon-tensor-vault_bd0e94"}}
            ),
            "lucid-beacon-tensor-vault_bd0e94",
        )
        self.assertIsNone(_config_node_name({"node": {"node_name": ""}}))
        self.assertEqual(_config_api_host({"api": {"host": 7}}), "127.0.0.1")
        self.assertEqual(_config_api_host({"api": {"host": "localhost"}}), "localhost")
        self.assertEqual(_config_api_host({}), "127.0.0.1")
        self.assertEqual(_config_api_port({"api": {"port": True}}), 7280)
        self.assertEqual(_config_api_port({"api": {"port": 9999}}), 9999)
        self.assertEqual(_config_api_port({}), 7280)
        self.assertFalse(_config_identity_persistence_enabled({}))
        self.assertTrue(
            _config_identity_persistence_enabled({"identity": {"persist": True}})
        )
        with self.assertRaisesRegex(RuntimeServiceError, "identity.persist"):
            _config_identity_persistence_enabled({"identity": {"persist": "yes"}})
        self.assertEqual(
            _config_identity_path({"identity": {}}, Path("home/id.json")),
            Path("home/id.json"),
        )
        self.assertEqual(
            _config_identity_path(
                {"identity": {"path": "identity.json"}}, Path("home/id.json")
            ),
            Path("home/identity.json"),
        )
        with self.assertRaisesRegex(RuntimeServiceError, "identity.path"):
            _config_identity_path({"identity": {"path": ""}}, Path("home/id.json"))
        self.assertEqual(
            _merge_config({"a": {"b": 2}, "c": 3}, {"a": {"d": 4}, "c": 0}),
            {"a": {"b": 2, "d": 4}, "c": 3},
        )

    def test_environment_and_platform_fallback_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"AETHERMESH_HOME": temp_dir}):
                self.assertEqual(_default_home(), Path(temp_dir))
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(_default_home(), Path.home() / ".aethermesh")

        self.assertEqual(_package_version(), "0.2.0-alpha")

        sysconf_calls: list[str] = []

        def fake_sysconf(name: str) -> int:
            sysconf_calls.append(name)
            return {"SC_PAGE_SIZE": 4096, "SC_PHYS_PAGES": 12345}[name]

        with (
            patch(
                "aethermesh_core.runtime_service.os.sysconf_names",
                {"SC_PAGE_SIZE": 1, "SC_PHYS_PAGES": 2},
            ),
            patch(
                "aethermesh_core.runtime_service.os.sysconf", side_effect=fake_sysconf
            ),
        ):
            self.assertEqual(_memory_total_bytes(), 4096 * 12345)
        self.assertEqual(sysconf_calls, ["SC_PAGE_SIZE", "SC_PHYS_PAGES"])

        for partial_names in [
            {"SC_PAGE_SIZE": 1},
            {"SC_PHYS_PAGES": 2},
        ]:
            with self.subTest(partial_names=partial_names):
                with (
                    patch(
                        "aethermesh_core.runtime_service.os.sysconf_names",
                        partial_names,
                    ),
                    patch("aethermesh_core.runtime_service.os.sysconf") as sysconf,
                ):
                    self.assertIsNone(_memory_total_bytes())
                    sysconf.assert_not_called()

        with patch(
            "aethermesh_core.runtime_service.os.kill", side_effect=PermissionError
        ):
            self.assertTrue(_pid_is_alive(123))
        with patch(
            "aethermesh_core.runtime_service.os.kill", side_effect=ProcessLookupError
        ):
            self.assertFalse(_pid_is_alive(123))
        with patch("aethermesh_core.runtime_service.os.sysconf", side_effect=OSError):
            self.assertIsNone(_memory_total_bytes())
        with patch("aethermesh_core.runtime_service.os.sysconf_names", {}):
            self.assertIsNone(_memory_total_bytes())
        with patch("aethermesh_core.runtime_service.os", types.SimpleNamespace()):
            self.assertIsNone(_memory_total_bytes())


class ApiTests(unittest.TestCase):
    def test_local_api_routes_return_service_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            service.initialize_local_node_data()

            payloads = asyncio.run(_fetch_api_payloads(create_app(service)))

            self.assertEqual(payloads["health"]["ok"], True)
            status_without_dynamic_system = dict(payloads["status"])
            status_alias_without_dynamic_system = dict(payloads["status_alias"])
            status_without_dynamic_system.pop("system")
            status_alias_without_dynamic_system.pop("system")
            self.assertEqual(
                status_alias_without_dynamic_system, status_without_dynamic_system
            )
            self.assertEqual(
                set(payloads["status_alias"]["system"]),
                set(payloads["status"]["system"]),
            )
            self.assertEqual(
                payloads["version_alias"]["version"], payloads["status"]["version"]
            )
            service_status = service.get_node_status()
            self.assertEqual(payloads["status"]["node_id"], service_status["node_id"])
            self.assertEqual(
                payloads["status"]["node_name"], service_status["node_name"]
            )
            self.assertEqual(
                payloads["status_alias"]["node_name"], service_status["node_name"]
            )
            node_without_dynamic_system = dict(payloads["node"])
            node_alias_without_dynamic_system = dict(payloads["node_alias"])
            node_without_dynamic_system.pop("system")
            node_alias_without_dynamic_system.pop("system")
            self.assertEqual(
                node_alias_without_dynamic_system, node_without_dynamic_system
            )
            self.assertEqual(
                set(payloads["node_alias"]["system"]), set(payloads["node"]["system"])
            )
            self.assertEqual(payloads["node"]["node_id"], service_status["node_id"])
            self.assertEqual(payloads["node"]["node_name"], service_status["node_name"])
            self.assertRegex(
                str(payloads["node"]["node_name"]),
                r"^[a-z]+-[a-z]+-[a-z]+-[a-z]+_[a-f0-9]{6}$",
            )
            self.assertEqual(
                str(payloads["node"]["node_name"]).rsplit("_", 1)[1],
                payloads["node"]["node_id"][:6],
            )
            self.assertEqual(payloads["node"]["status"], "stopped")
            self.assertEqual(payloads["peers"], payloads["peers_alias"])
            self.assertEqual(payloads["peers"]["peers"], [])
            self.assertEqual(payloads["jobs"]["current"], [])
            self.assertEqual(payloads["capabilities"], payloads["capabilities_alias"])
            self.assertEqual(
                payloads["capabilities"]["capabilities"],
                ["echo", "keyword_extract", "text_chunk", "text_embed", "text_stats"],
            )
            self.assertEqual(payloads["package"]["name"], "aethermesh")
            self.assertEqual(payloads["package"]["source"], "installed")
            self.assertEqual(payloads["network"]["status"], "local_only")
            self.assertTrue(payloads["network"]["localhost_only"])
            self.assertEqual(payloads["logs"], payloads["logs_alias"])
            self.assertIn("events", payloads["logs"])
            self.assertIn("events", payloads["events"])
            self.assertEqual(payloads["shutdown"]["shutdown_requested"], True)
            self.assertEqual(payloads["restart"]["restart_requested"], True)
            self.assertIn("AetherMesh Local Node", payloads["html"])
            self.assertIn("/api/status", payloads["html"])
            self.assertIn("Node Name", payloads["html"])
            self.assertIn("status.node_name", payloads["html"])
            self.assertIn("textContent", payloads["html"])
            self.assertNotIn("innerHTML", payloads["html"])

            self.assertEqual(
                set(payloads["health"]),
                {
                    "ok",
                    "service",
                    "version",
                    "status",
                    "bind_host",
                    "port",
                    "config_path",
                },
            )
            self.assertEqual(payloads["health"]["service"], "aethermesh-local-node")
            self.assertEqual(payloads["health"]["status"], "stopped")
            self.assertEqual(payloads["health"]["bind_host"], "127.0.0.1")
            self.assertEqual(payloads["health"]["port"], 7280)
            self.assertEqual(
                payloads["health"]["config_path"], str(service.paths.config_path)
            )

            api = create_app(service)
            self.assertEqual(api.title, "AetherMesh Local Node API")
            self.assertEqual(api.version, "0.2.0-alpha")
            self.assertIs(api.router.lifespan_context, _lifespan)

    def test_lifespan_uses_same_runtime_service(self) -> None:
        async def exercise() -> None:
            with tempfile.TemporaryDirectory() as temp_dir:
                service = NodeRuntimeService.from_home(Path(temp_dir))
                api = create_app(service)
                async with _lifespan(api):
                    self.assertEqual(service.get_node_status()["status"], "running")
                self.assertEqual(service.get_node_status()["status"], "stopped")

        asyncio.run(exercise())


class AppCliTests(unittest.TestCase):
    def test_cli_smoke_commands_use_runtime_service(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CliRunner(env={"AETHERMESH_HOME": temp_dir})

            version = runner.invoke(app_cli.app, ["--version"])
            self.assertEqual(version.exit_code, 0)
            self.assertIn("0.2.0-alpha", version.output)

            init = runner.invoke(app_cli.app, ["init"])
            self.assertEqual(init.exit_code, 0)
            self.assertIn("Initialized AetherMesh", init.output)

            for args, expected in [
                (["status"], "stopped"),
                (["node", "status"], "stopped"),
                (["node", "stop"], "Marked foreground"),
                (["peers"], "No peers discovered"),
                (["jobs"], "No current jobs"),
            ]:
                result = runner.invoke(app_cli.app, args)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIn(expected, result.output)

            ui = runner.invoke(app_cli.app, ["ui", "--dry-run"])
            self.assertEqual(ui.exit_code, 0)
            self.assertIn("http://127.0.0.1:7280", ui.output)

    def test_cli_node_start_dry_run_reports_localhost_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CliRunner(env={"AETHERMESH_HOME": temp_dir})
            result = runner.invoke(app_cli.app, ["node", "start", "--dry-run"])

            self.assertEqual(result.exit_code, 0)
            self.assertIn("127.0.0.1", result.output)
            self.assertIn("7280", result.output)

    def test_cli_node_start_stop_delegate_to_background_manager(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_dir = Path(temp_dir) / "config"
            settings_dir.mkdir(parents=True)
            (settings_dir / "desktop-settings.json").write_text(
                json.dumps({"backgroundNodeEnabled": True}), encoding="utf-8"
            )
            calls: list[list[str]] = []

            def fake_run(command: list[str], **_: object) -> object:
                calls.append(command)
                return types.SimpleNamespace(stdout="", stderr="")

            runner = CliRunner(env={"AETHERMESH_HOME": temp_dir})
            with (
                patch("aethermesh_core.app_cli.sys_platform", return_value="linux"),
                patch("aethermesh_core.app_cli.subprocess.run", side_effect=fake_run),
            ):
                start = runner.invoke(app_cli.app, ["node", "start"])
                stop = runner.invoke(app_cli.app, ["node", "stop"])

            self.assertEqual(start.exit_code, 0, start.output)
            self.assertEqual(stop.exit_code, 0, stop.output)
            self.assertEqual(
                calls,
                [
                    ["systemctl", "--user", "start", "aethermesh-node.service"],
                    ["systemctl", "--user", "stop", "aethermesh-node.service"],
                ],
            )

    def test_cli_node_start_reuses_existing_local_api(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CliRunner(env={"AETHERMESH_HOME": temp_dir})
            with (
                patch(
                    "aethermesh_core.app_cli._local_api_is_aethermesh",
                    return_value=True,
                ),
                patch("aethermesh_core.app_cli._serve") as serve,
            ):
                result = runner.invoke(app_cli.app, ["node", "start"])
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("already running", result.output)
            serve.assert_not_called()

    def test_background_control_helper_platforms_and_errors(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], **_: object) -> object:
            calls.append(command)
            return types.SimpleNamespace(stdout="", stderr="")

        with patch("aethermesh_core.app_cli.subprocess.run", side_effect=fake_run):
            with patch("aethermesh_core.app_cli.os.name", "nt"):
                app_cli._control_background_node("start")
                app_cli._control_background_node("stop")
            with patch("aethermesh_core.app_cli.sys_platform", return_value="darwin"):
                app_cli._control_background_node("start")
                app_cli._control_background_node("stop")

        self.assertEqual(calls[0], ["schtasks.exe", "/Run", "/TN", "AetherMesh Node"])
        self.assertEqual(calls[1], ["schtasks.exe", "/End", "/TN", "AetherMesh Node"])
        self.assertEqual(calls[2][:3], ["launchctl", "kickstart", "-k"])
        self.assertEqual(calls[3][:3], ["launchctl", "kill", "TERM"])
        self.assertIsInstance(app_cli.sys_platform(), str)

        with self.assertRaisesRegex(
            RuntimeServiceError, "unsupported background action"
        ):
            app_cli._control_background_node("restart")

        failure = subprocess.CalledProcessError(
            1, ["systemctl"], output="", stderr="nope"
        )
        with (
            patch("aethermesh_core.app_cli.sys_platform", return_value="linux"),
            patch("aethermesh_core.app_cli.subprocess.run", side_effect=failure),
            self.assertRaisesRegex(Exception, "could not start background node: nope"),
        ):
            app_cli._control_background_node("start")

    def test_local_api_health_detection_handles_false_paths(self) -> None:
        self.assertFalse(app_cli._local_api_is_aethermesh(host="0.0.0.0", port=7280))
        self.assertFalse(app_cli._local_api_is_aethermesh(host="127.0.0.1", port=1))

        class FakeResponse:
            def __init__(self, payload: bytes) -> None:
                self._payload = payload

            def read(self) -> bytes:
                return self._payload

        class FakeConnection:
            def __init__(self, host: str, port: int, timeout: float) -> None:
                self.host = host
                self.port = port
                self.timeout = timeout
                self.closed = False
                self.payload = b'{"service":"not-aethermesh"}'

            def request(self, method: str, target: str) -> None:
                self.method = method
                self.target = target

            def getresponse(self) -> FakeResponse:
                return FakeResponse(self.payload)

            def close(self) -> None:
                self.closed = True

        fake = FakeConnection("127.0.0.1", 7280, 0.5)
        with patch(
            "aethermesh_core.app_cli.http.client.HTTPConnection", return_value=fake
        ):
            self.assertFalse(
                app_cli._local_api_is_aethermesh(host="127.0.0.1", port=7280)
            )
        self.assertEqual(fake.method, "GET")
        self.assertEqual(fake.target, "/health")
        self.assertTrue(fake.closed)

        fake_ok = FakeConnection("127.0.0.1", 7280, 0.5)
        fake_ok.payload = b'{"service":"aethermesh-local-node"}'
        with patch(
            "aethermesh_core.app_cli.http.client.HTTPConnection", return_value=fake_ok
        ):
            self.assertTrue(
                app_cli._local_api_is_aethermesh(host="127.0.0.1", port=7280)
            )

        with patch(
            "aethermesh_core.app_cli.http.client.HTTPConnection",
            side_effect=OSError("no listener"),
        ):
            self.assertFalse(
                app_cli._local_api_is_aethermesh(host="127.0.0.1", port=7280)
            )

    def test_cli_update_installs_latest_release_and_reports_errors(self) -> None:
        class FakeUpdateResult:
            def __init__(self, *, installed: bool) -> None:
                self.installed = installed

            def to_dict(self) -> dict[str, object]:
                return {
                    "release_tag": "v0.2.0-alpha-abc123",
                    "release_name": "0.2.0-alpha - (...bc123)",
                    "release_url": "https://github.example/release",
                    "wheel_name": "aethermesh-0.2.0a0-py3-none-any.whl",
                    "wheel_url": "https://github.example/aethermesh.whl",
                    "sha256": "abc123",
                    "expected_sha256": "abc123",
                    "installed": self.installed,
                }

        runner = CliRunner()
        with patch(
            "aethermesh_core.app_cli.update_from_latest_release",
            return_value=FakeUpdateResult(installed=False),
        ) as updater:
            result = runner.invoke(app_cli.app, ["update", "--dry-run"])

        self.assertEqual(result.exit_code, 0, result.output)
        updater.assert_called_once_with(dry_run=True, release_url=None)
        self.assertIn("v0.2.0-alpha-abc123", result.output)
        self.assertIn("verified", result.output)
        self.assertIn("not installed", result.output)

        with patch(
            "aethermesh_core.app_cli.update_from_latest_release",
            return_value=FakeUpdateResult(installed=True),
        ) as updater:
            result = runner.invoke(app_cli.app, ["update"])

        self.assertEqual(result.exit_code, 0, result.output)
        updater.assert_called_once_with(dry_run=False, release_url=None)
        self.assertIn("Installed latest AetherMesh release", result.output)

        with patch(
            "aethermesh_core.app_cli.update_from_latest_release",
            side_effect=ReleaseUpdateError("network sad"),
        ):
            result = runner.invoke(app_cli.app, ["update"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("network sad", result.output)

    def test_cli_warning_and_table_branches_are_exercised(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runner = CliRunner(env={"AETHERMESH_HOME": temp_dir})

            start = runner.invoke(
                app_cli.app,
                ["node", "start", "--host", "0.0.0.0", "--dry-run"],
            )
            self.assertEqual(start.exit_code, 0)
            self.assertIn("non-localhost", start.output)

            class FakeService:
                def list_peers(self) -> dict[str, object]:
                    return {
                        "peers": [
                            {
                                "node_id": "peer-a",
                                "status": "available",
                                "capabilities": ["echo"],
                            }
                        ]
                    }

                def list_jobs(self) -> dict[str, object]:
                    return {
                        "current": [{"job_id": "job-a"}],
                        "completed": [{"job_id": "job-b"}],
                        "failed": [{"job_id": "job-c"}],
                        "note": "active",
                    }

            with patch.object(
                app_cli.NodeRuntimeService, "default", return_value=FakeService()
            ):
                self.assertIn("peer-a", runner.invoke(app_cli.app, ["peers"]).output)
                self.assertNotIn(
                    "No current jobs", runner.invoke(app_cli.app, ["jobs"]).output
                )

            with app_cli.console.capture() as status_capture:
                app_cli._print_status({"api": "not-a-dict"})
            status_output = status_capture.get()
            self.assertIn("AetherMesh Node Status", status_output)
            self.assertIn("Field", status_output)
            self.assertIn("Value", status_output)
            self.assertIn("node_id", status_output)
            self.assertNotIn("http://", status_output)

            with app_cli.console.capture() as api_status_capture:
                app_cli._print_status(
                    {
                        "node_id": "node-a",
                        "status": "running",
                        "version": "9.9.9",
                        "uptime_seconds": 42,
                        "config_path": "/tmp/aethermesh/config.json",
                        "data_dir": "/tmp/aethermesh/data",
                        "peer_count": 3,
                        "api": {"host": "localhost", "port": 9999},
                    }
                )
            api_status_output = api_status_capture.get()
            for expected in [
                "node-a",
                "running",
                "9.9.9",
                "42",
                "/tmp/aethermesh/config.json",
                "/tmp/aethermesh/data",
                "3",
                "http://localhost:9999",
            ]:
                self.assertIn(expected, api_status_output)

            class FakeTable:
                def __init__(self, title: str) -> None:
                    self.title = title
                    self.columns: list[str] = []
                    self.rows: list[tuple[str, ...]] = []

                def add_column(self, name: str) -> None:
                    self.columns.append(name)

                def add_row(self, *values: str) -> None:
                    self.rows.append(values)

            printed: list[FakeTable] = []
            with (
                patch.object(app_cli, "Table", FakeTable),
                patch.object(app_cli.console, "print", side_effect=printed.append),
            ):
                app_cli._print_status(
                    {
                        "node_id": "node-a",
                        "status": "running",
                        "version": "9.9.9",
                        "uptime_seconds": 42,
                        "config_path": "/tmp/aethermesh/config.json",
                        "data_dir": "/tmp/aethermesh/data",
                        "peer_count": 3,
                        "api": {"host": "localhost", "port": 9999},
                    }
                )
            self.assertEqual(len(printed), 1)
            self.assertEqual(printed[0].title, "AetherMesh Node Status")
            self.assertEqual(printed[0].columns, ["Field", "Value"])
            self.assertEqual(printed[0].rows[-1], ("api", "http://localhost:9999"))

    def test_serve_uses_uvicorn_and_reports_missing_ui_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            calls: dict[str, object] = {}
            timer_calls: list[dict[str, object]] = []
            browser_urls: list[str] = []

            def fake_run(api: FastAPI, host: str, port: int, log_level: str) -> None:
                self.assertIsInstance(api, FastAPI)
                self.assertEqual(log_level, "info")
                calls.update(
                    {"app": api, "host": host, "port": port, "log_level": log_level}
                )

            class FakeTimer:
                def __init__(self, interval: float, function: object) -> None:
                    self.interval = interval
                    self.function = function

                def start(self) -> None:
                    self.assert_timer_shape()
                    timer_calls.append(
                        {"interval": self.interval, "function": self.function}
                    )
                    assert callable(self.function)
                    self.function()

                def assert_timer_shape(self) -> None:
                    if self.interval != 0.8:
                        raise AssertionError(self.interval)
                    if not callable(self.function):
                        raise AssertionError(self.function)

            fake_uvicorn = types.SimpleNamespace(run=fake_run)
            with (
                patch.dict(sys.modules, {"uvicorn": fake_uvicorn}),
                patch.dict(os.environ, {"AETHERMESH_HOME": temp_dir}),
                patch(
                    "aethermesh_core.app_cli.threading.Timer",
                    side_effect=lambda interval, function: FakeTimer(
                        interval, function
                    ),
                ),
                patch(
                    "aethermesh_core.app_cli.webbrowser.open",
                    side_effect=lambda url: browser_urls.append(url),
                ),
            ):
                with app_cli.console.capture() as warning_capture:
                    app_cli._serve(host="0.0.0.0", port=7777, open_browser=True)
                self.assertIn(
                    "Warning: non-localhost API binding is not the safe default.",
                    warning_capture.get(),
                )
                self.assertEqual(calls["host"], "0.0.0.0")
                self.assertEqual(calls["port"], 7777)
                self.assertEqual(calls["log_level"], "info")
                self.assertEqual(len(timer_calls), 1)
                self.assertEqual(timer_calls[0]["interval"], 0.8)
                self.assertEqual(browser_urls, ["http://0.0.0.0:7777"])
                with app_cli.console.capture() as localhost_capture:
                    app_cli._serve(host="127.0.0.1", port=7280, open_browser=False)
                self.assertNotIn("non-localhost", localhost_capture.get())
                self.assertEqual(calls["host"], "127.0.0.1")
                with app_cli.console.capture() as localhost_name_capture:
                    app_cli._serve(host="localhost", port=7281, open_browser=False)
                self.assertNotIn("non-localhost", localhost_name_capture.get())
                self.assertEqual(calls["host"], "localhost")
                self.assertEqual(calls["port"], 7281)

            with (
                patch(
                    "aethermesh_core.app_cli._local_api_is_aethermesh",
                    return_value=False,
                ),
                patch("aethermesh_core.app_cli._serve") as serve,
            ):
                CliRunner(env={"AETHERMESH_HOME": temp_dir}).invoke(
                    app_cli.app, ["node", "start"]
                )
                serve.assert_called_with(
                    host="127.0.0.1", port=7280, open_browser=False
                )
                CliRunner(env={"AETHERMESH_HOME": temp_dir}).invoke(
                    app_cli.app, ["ui", "--no-open"]
                )
                serve.assert_called_with(
                    host="127.0.0.1", port=7280, open_browser=False
                )

            real_import = builtins.__import__

            def blocked_import(
                name: str,
                globals: dict[str, object] | None = None,
                locals: dict[str, object] | None = None,
                fromlist: tuple[str, ...] = (),
                level: int = 0,
            ) -> object:
                if name == "uvicorn":
                    raise ImportError("blocked")
                return real_import(name, globals, locals, fromlist, level)

            with patch("builtins.__import__", side_effect=blocked_import):
                with self.assertRaisesRegex(
                    Exception, "API/UI dependencies are missing"
                ):
                    app_cli._serve(host="127.0.0.1", port=7280, open_browser=False)


if __name__ == "__main__":
    unittest.main()
