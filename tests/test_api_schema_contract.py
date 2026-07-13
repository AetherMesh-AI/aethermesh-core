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
            examples = [
                json.loads(block)
                for block in re.findall(r"```json\n(.*?)\n```", contract, re.DOTALL)
            ]
            self.assertEqual(len(examples), 4)
            submission, status_example, receipt_example, contribution_example = examples
            self.assertEqual(submission, request)
            self.assertEqual(
                set(status_example),
                {
                    "schema_version",
                    "job_id",
                    "status",
                    "manifest_ref",
                    "creator_node_id",
                    "requested_capability",
                    "requester_identity",
                    "worker_node_id",
                    "lineage",
                    "contribution_attribution",
                    "validation",
                    "result",
                    "error",
                    "network_mode",
                },
            )
            self.assertTrue(
                {
                    "schema_version",
                    "receipt_id",
                    "work_id",
                    "creator_node_id",
                    "requester_identity",
                    "manifest_ref",
                    "lineage_parent_ids",
                    "validation_status",
                    "validator_identity",
                    "validator_software",
                    "contribution_attribution",
                    "validation_scope",
                    "validation",
                    "evidence",
                }.issubset(receipt_example)
            )
            self.assertTrue(
                {
                    "work_item_id",
                    "status",
                    "acceptance_status",
                    "creator_node_id",
                    "contributing_node_id",
                    "manifest_ref",
                    "status_ref",
                    "validation_receipt_ref",
                    "lineage_links",
                    "timestamps",
                    "evidence_errors",
                }.issubset(contribution_example["items"][0])
            )

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
            accepted_payload = accepted.json()
            self.assertEqual(accepted_payload["status"], "accepted")
            self.assertEqual(
                accepted_payload["creator_node_id"], request["creator_node_id"]
            )
            self.assertTrue(accepted_payload["manifest_ref"])
            self.assertTrue(accepted_payload["attribution_ref"])
            for response in (
                missing_version,
                boolean_version,
                missing_creator,
                missing_lineage,
                missing_attribution,
            ):
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "rejected")
                self.assertEqual(response.json()["validation"]["state"], "rejected")

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
            self.assertEqual(
                set(status_payload["validation"]), set(status_example["validation"])
            )
            self.assertEqual(
                set(status_payload["result"]), set(status_example["result"])
            )
            self.assertEqual(receipt.status_code, 200)
            self.assertEqual(receipt.json()["schema_version"], 5)
            self.assertEqual(receipt.json()["status"], "accepted")
            self.assertIsNone(receipt.json()["rejection_reason"])
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

            documented_operations = {
                ("/api/jobs", "get"),
                ("/api/jobs", "post"),
                ("/api/jobs/{job_id}", "get"),
                ("/api/validation-receipts", "get"),
                ("/api/contributions", "get"),
                ("/api/audit-events", "get"),
            }
            self.assertTrue(
                all(
                    method in openapi["paths"].get(route, {})
                    for route, method in documented_operations
                )
            )


if __name__ == "__main__":
    unittest.main()
