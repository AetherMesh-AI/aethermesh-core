import asyncio
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from aethermesh_core.api import create_app
from aethermesh_core.runtime_service import NodeRuntimeService


class ApiErrorTests(unittest.TestCase):
    def test_failures_have_safe_structured_errors_and_local_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            manifest_dir = service.paths.data_dir / "job-submissions"
            manifest_dir.mkdir(parents=True)
            manifest_dir.joinpath("local-job-secret.json").write_text(
                '{"creator_node_id":"creator-secret","lineage":{"token":"hidden"}}',
                encoding="utf-8",
            )
            app = create_app(service)

            async def exercise() -> tuple[httpx.Response, ...]:
                transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    responses = (
                        await client.post("/api/jobs", json=[]),
                        await client.get("/api/missing-route"),
                        await client.post("/health"),
                        await client.get("/api/audit-events"),
                        await client.get(
                            "/api/validation-receipts", params={"work_id": "bad"}
                        ),
                        await client.get(
                            "/api/audit-events", params={"lineage_id": ""}
                        ),
                        await client.get(
                            "/api/audit-events",
                            params={"contribution_attribution_id": ""},
                        ),
                    )
                    with self.assertLogs("aethermesh_core.api", level="ERROR") as logs:
                        internal = await client.get("/api/jobs")
                    self.assertIn("unexpected-local-secret", "\n".join(logs.output))
                    return (*responses, internal)

            with patch.object(
                service,
                "list_jobs",
                side_effect=RuntimeError("unexpected-local-secret"),
            ):
                responses = asyncio.run(exercise())

            expected_codes = (
                "INVALID_INPUT",
                "NOT_FOUND",
                "INVALID_INPUT",
                "MISSING_MANIFEST",
                "VALIDATION_FAILURE",
                "LINEAGE_LOOKUP_FAILURE",
                "CONTRIBUTION_ATTRIBUTION_FAILURE",
                "INTERNAL_ERROR",
            )
            sensitive_values = ("creator-secret", "hidden", "unexpected-local-secret")
            for response, expected_code in zip(responses, expected_codes, strict=True):
                self.assertIn(response.status_code, {400, 404, 405, 500})
                payload = response.json()
                self.assertEqual(set(payload), {"error", "request_id"})
                self.assertEqual(set(payload["error"]), {"code", "message", "details"})
                self.assertEqual(payload["error"]["code"], expected_code)
                self.assertEqual(payload["error"]["details"], {})
                self.assertRegex(payload["request_id"], re.compile(r"^[0-9a-f]{32}$"))
                self.assertTrue(
                    all(value not in response.text for value in sensitive_values)
                )

    def test_invalid_api_inputs_fail_closed_without_local_artifact_mutation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            service = NodeRuntimeService.from_home(home)
            app = create_app(service)
            valid_request = {
                "schema_version": 1,
                "job_type": "echo",
                "payload": {"message": "safe"},
                "creator_node_id": "creator-local-a",
                "requested_validation_mode": "deterministic-local",
                "lineage_parent_refs": [],
                "attribution_metadata": {},
            }

            def local_artifacts() -> dict[str, bytes]:
                data_dir = home / "data"
                return (
                    {
                        str(path.relative_to(home)): path.read_bytes()
                        for path in data_dir.rglob("*")
                        if path.is_file()
                    }
                    if data_dir.exists()
                    else {}
                )

            async def exercise() -> tuple[httpx.Response, ...]:
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    return (
                        await client.post(
                            "/api/jobs",
                            json={
                                key: value
                                for key, value in valid_request.items()
                                if key != "creator_node_id"
                            },
                        ),
                        await client.post(
                            "/api/jobs",
                            json={**valid_request, "payload": []},
                        ),
                        await client.post(
                            "/api/jobs",
                            json={**valid_request, "creator_node_id": "../creator"},
                        ),
                        await client.post(
                            "/api/jobs",
                            json={
                                **valid_request,
                                "lineage_parent_refs": ["../outside.json"],
                            },
                        ),
                        await client.post(
                            "/api/jobs",
                            json={**valid_request, "attribution_metadata": []},
                        ),
                        await client.get("/api/jobs/not-a-local-job-id"),
                        await client.get(
                            "/api/validation-receipts",
                            params={"receipt_id": "not-a-local-receipt"},
                        ),
                        await client.get(
                            "/api/audit-events",
                            params={"manifest_id": "not-a-local-job-id"},
                        ),
                        await client.get(
                            "/api/audit-events",
                            params={"lineage_id": "not-a-local-lineage-id"},
                        ),
                        await client.get(
                            "/api/audit-events",
                            params={
                                "contribution_attribution_id": "not-a-local-attribution-id"
                            },
                        ),
                    )

            before = local_artifacts()
            responses = asyncio.run(exercise())
            self.assertEqual(local_artifacts(), before)
            for response in responses:
                self.assertEqual(response.status_code, 400)
                payload = response.json()
                self.assertEqual(payload["error"]["details"], {})
                self.assertNotIn("creator-local-a", response.text)
                self.assertNotIn("outside.json", response.text)


if __name__ == "__main__":
    unittest.main()
