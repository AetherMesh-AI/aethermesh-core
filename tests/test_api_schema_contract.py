import asyncio
import json
import re
import tempfile
import unittest
from pathlib import Path

import httpx

from aethermesh_core.api import create_app
from aethermesh_core.runtime_service import NodeRuntimeService


class ApiSchemaContractTests(unittest.TestCase):
    def test_documented_submission_example_and_provenance_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            app = create_app(service)
            contract = (
                Path(__file__).parents[1] / "docs" / "phase-1-api-schema-contract.md"
            ).read_text(encoding="utf-8")
            example_match = re.search(
                r"## Local Job Submission v1.*?Example request:\n\n```json\n(.*?)\n```",
                contract,
                re.DOTALL,
            )
            if example_match is None:
                self.fail("submission example is missing from schema contract")
            request = json.loads(example_match.group(1))

            async def exercise() -> tuple[httpx.Response, ...]:
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    accepted = await client.post("/api/jobs", json=request)
                    job_id = accepted.json()["job_id"]
                    service.execute_submitted_local_job(job_id, "worker-local-example")
                    return (
                        accepted,
                        await client.post(
                            "/api/jobs",
                            json={
                                key: value
                                for key, value in request.items()
                                if key != "schema_version"
                            },
                        ),
                        await client.post(
                            "/api/jobs", json={**request, "schema_version": True}
                        ),
                        await client.post(
                            "/api/jobs",
                            json={
                                key: value
                                for key, value in request.items()
                                if key != "creator_node_id"
                            },
                        ),
                        await client.post(
                            "/api/jobs",
                            json={
                                key: value
                                for key, value in request.items()
                                if key != "lineage_parent_refs"
                            },
                        ),
                        await client.post(
                            "/api/jobs",
                            json={
                                key: value
                                for key, value in request.items()
                                if key != "attribution_metadata"
                            },
                        ),
                        await client.get(f"/api/jobs/{job_id}"),
                        await client.get(
                            "/api/validation-receipts", params={"work_id": job_id}
                        ),
                        await client.get("/api/contributions"),
                    )

            (
                accepted,
                missing_version,
                boolean_version,
                missing_creator,
                missing_lineage,
                missing_attribution,
                status,
                receipt,
                contributions,
            ) = asyncio.run(exercise())
            openapi = app.openapi()

            self.assertEqual(accepted.status_code, 200)
            self.assertEqual(accepted.json()["schema_version"], 1)
            self.assertEqual(accepted.json()["status"], "accepted_pending_execution")
            for response, field in (
                (missing_version, "schema_version"),
                (boolean_version, "schema_version"),
                (missing_creator, "creator_node_id"),
                (missing_lineage, "lineage_parent_refs"),
                (missing_attribution, "attribution_metadata"),
            ):
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json()["detail"])

            status_payload = status.json()
            self.assertEqual(status_payload["schema_version"], 1)
            self.assertEqual(status_payload["status"], "succeeded")
            self.assertEqual(
                status_payload["creator_node_id"], request["creator_node_id"]
            )
            self.assertEqual(
                status_payload["lineage"]["parent_refs"], request["lineage_parent_refs"]
            )
            self.assertEqual(
                status_payload["contribution_attribution"]["metadata"],
                request["attribution_metadata"],
            )
            self.assertTrue(status_payload["validation"]["passed"])
            self.assertEqual(receipt.status_code, 200)
            self.assertEqual(receipt.json()["schema_version"], 1)
            self.assertEqual(receipt.json()["work_id"], accepted.json()["job_id"])
            self.assertEqual(
                receipt.json()["creator_node_id"], request["creator_node_id"]
            )
            self.assertEqual(
                receipt.json()["lineage_parent_ids"], request["lineage_parent_refs"]
            )
            self.assertEqual(contributions.status_code, 200)
            self.assertEqual(contributions.json()["schema_version"], 1)
            self.assertEqual(contributions.json()["accepted_work_count"], 1)

            documented_routes = {
                "/api/jobs",
                "/api/jobs/{job_id}",
                "/api/validation-receipts",
                "/api/contributions",
                "/api/audit-events",
            }
            self.assertTrue(documented_routes.issubset(openapi["paths"]))


if __name__ == "__main__":
    unittest.main()
