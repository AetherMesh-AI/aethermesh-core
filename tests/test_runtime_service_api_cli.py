import asyncio
import builtins
import json
import os
import sys
import tempfile
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
            "node": (await client.get("/api/node")).json(),
            "peers": (await client.get("/api/peers")).json(),
            "jobs": (await client.get("/api/jobs")).json(),
            "logs": (await client.get("/api/logs")).json(),
            "events": (await client.get("/api/events")).json(),
            "html": (await client.get("/")).text,
        }


class RuntimeServiceTests(unittest.TestCase):
    def test_init_creates_reusable_local_node_data_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))

            initialized = service.initialize_local_node_data()
            status = service.get_node_status()

            self.assertEqual(
                initialized["config_path"], str(Path(temp_dir) / "config.json")
            )
            self.assertTrue(Path(initialized["identity_path"]).exists())
            self.assertTrue(status["initialized"])
            self.assertEqual(status["status"], "stopped")
            self.assertEqual(status["api"]["host"], "127.0.0.1")
            self.assertEqual(status["api"]["port"], 7280)
            self.assertEqual(status["peer_count"], 0)
            self.assertEqual(
                status["job_counts"], {"current": 0, "completed": 0, "failed": 0}
            )

            config = json.loads((Path(temp_dir) / "config.json").read_text())
            self.assertEqual(config["version"], 1)
            self.assertEqual(config["node"]["node_id"], status["node_id"])

    def test_peers_jobs_and_health_are_honest_when_node_has_no_runtime_work(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            service.initialize_local_node_data()

            self.assertEqual(service.list_peers()["peers"], [])
            self.assertEqual(service.list_peers()["bootstrap_status"], "not_configured")
            self.assertEqual(service.list_jobs()["current"], [])
            self.assertEqual(service.list_jobs()["completed"], [])
            self.assertEqual(service.list_jobs()["failed"], [])
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
        self.assertEqual(_config_api_host({"api": {"host": 7}}), "127.0.0.1")
        self.assertEqual(_config_api_port({"api": {"port": True}}), 7280)
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
            self.assertEqual(
                payloads["status"]["node_id"], service.get_node_status()["node_id"]
            )
            self.assertEqual(payloads["node"]["status"], "stopped")
            self.assertEqual(payloads["peers"]["peers"], [])
            self.assertEqual(payloads["jobs"]["current"], [])
            self.assertIn("events", payloads["logs"])
            self.assertIn("events", payloads["events"])
            self.assertIn("AetherMesh Local Node", payloads["html"])
            self.assertIn("/api/status", payloads["html"])

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

            app_cli._print_status({"api": "not-a-dict"})

    def test_serve_uses_uvicorn_and_reports_missing_ui_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            calls: dict[str, object] = {}
            fake_uvicorn = types.SimpleNamespace(
                run=lambda api, host, port, log_level: calls.update(
                    {"app": api, "host": host, "port": port, "log_level": log_level}
                )
            )
            fake_timer = types.SimpleNamespace(start=lambda: None)
            with (
                patch.dict(sys.modules, {"uvicorn": fake_uvicorn}),
                patch.dict(os.environ, {"AETHERMESH_HOME": temp_dir}),
                patch(
                    "aethermesh_core.app_cli.threading.Timer", return_value=fake_timer
                ),
            ):
                app_cli._serve(host="0.0.0.0", port=7777, open_browser=True)
                self.assertEqual(calls["host"], "0.0.0.0")
                self.assertEqual(calls["port"], 7777)
                app_cli._serve(host="127.0.0.1", port=7280, open_browser=False)
                self.assertEqual(calls["host"], "127.0.0.1")

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
