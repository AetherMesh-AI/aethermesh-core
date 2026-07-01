import asyncio
import builtins
import json
import os
import sys
import tempfile
import time
import types
import unittest
from importlib import metadata
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
    _config_node_id,
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
                    "home",
                    "config_path",
                    "data_dir",
                    "log_dir",
                    "identity_path",
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
            self.assertTrue(Path(initialized["identity_path"]).exists())
            self.assertEqual(
                service.recent_logs(limit=1)["events"][0].split(" ", 1)[1],
                "initialized local node data",
            )
            self.assertEqual(
                set(status),
                {
                    "initialized",
                    "node_id",
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
            self.assertEqual(config["node"]["status"], "local_only")
            self.assertEqual(config["paths"]["home"], str(Path(temp_dir)))
            self.assertEqual(config["paths"]["data_dir"], str(Path(temp_dir) / "data"))
            self.assertEqual(config["paths"]["log_dir"], str(Path(temp_dir) / "logs"))
            self.assertEqual(config["api"], {"host": "127.0.0.1", "port": 7280})

            with patch.object(
                service, "_runtime_marker", return_value=(False, None, int(time.time()))
            ):
                self.assertIsNone(service.get_node_status()["uptime_seconds"])

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
            self.assertTrue(service.paths.identity_path.exists())

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
            self.assertTrue(service.paths.identity_path.exists())

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
        self.assertEqual(_config_api_host({"api": {"host": 7}}), "127.0.0.1")
        self.assertEqual(_config_api_host({"api": {"host": "localhost"}}), "localhost")
        self.assertEqual(_config_api_host({}), "127.0.0.1")
        self.assertEqual(_config_api_port({"api": {"port": True}}), 7280)
        self.assertEqual(_config_api_port({"api": {"port": 9999}}), 9999)
        self.assertEqual(_config_api_port({}), 7280)
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

        with patch("aethermesh_core.runtime_service.metadata.version") as version:
            version.side_effect = metadata.PackageNotFoundError
            self.assertEqual(_package_version(), "0.1.0")

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
            self.assertEqual(payloads["status_alias"], payloads["status"])
            self.assertEqual(
                payloads["version_alias"]["version"], payloads["status"]["version"]
            )
            self.assertEqual(
                payloads["status"]["node_id"], service.get_node_status()["node_id"]
            )
            self.assertEqual(payloads["node"], payloads["node_alias"])
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
            self.assertEqual(api.version, "0.1.0")
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
            self.assertIn("0.1.0", version.output)

            init = runner.invoke(app_cli.app, ["init"])
            self.assertEqual(init.exit_code, 0)
            self.assertIn("Initialized AetherMesh", init.output)

            for args, expected in [
                (["status"], "stopped"),
                (["node", "status"], "stopped"),
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

    def test_cli_update_installs_latest_release_and_reports_errors(self) -> None:
        class FakeUpdateResult:
            def __init__(self, *, installed: bool) -> None:
                self.installed = installed

            def to_dict(self) -> dict[str, object]:
                return {
                    "release_tag": "v0.1.1-alpha-abc123",
                    "release_name": "0.1.1-alpha (abc123)",
                    "release_url": "https://github.example/release",
                    "wheel_name": "aethermesh-0.1.0a0-py3-none-any.whl",
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
        self.assertIn("v0.1.1-alpha-abc123", result.output)
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

            with patch("aethermesh_core.app_cli._serve") as serve:
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
