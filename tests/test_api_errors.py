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
                    with self.assertLogs("aethermesh_core.api", level="ERROR") as logs:
                        internal = await client.get("/api/jobs")
                    self.assertIn("unexpected-local-secret", "\n".join(logs.output))
                    return (
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
                        internal,
                    )

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


if __name__ == "__main__":
    unittest.main()
