import asyncio
import json
import tempfile
import unittest
from pathlib import Path

import httpx

from aethermesh_core.api import create_app
from aethermesh_core.runtime_service import NodeRuntimeService, RuntimeServiceError


class AuditInspectionTests(unittest.TestCase):
    def test_inspection_filters_evidence_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            service = NodeRuntimeService.from_home(home)
            accepted = service.submit_local_job(
                {
                    "job_type": "echo",
                    "input_payload": {
                        "payload_type": "json",
                        "content": {"message": "audit"},
                    },
                    "creator_node_id": "creator-local-a",
                    "requested_validation_mode": "deterministic-local",
                    "schema_version": 1,
                    "lineage_parent_refs": ["data/prior-job.json"],
                    "attribution_metadata": {"project": "prototype"},
                }
            )
            service.execute_submitted_local_job(accepted["job_id"], "worker-local-a")
            before = {
                str(path.relative_to(home)): path.read_bytes()
                for path in home.rglob("*.json")
            }

            audit = service.inspect_local_audit_events(
                manifest_id=accepted["job_id"], node_id="worker-local-a", limit=1
            )
            event = audit["events"][0]
            filtered = service.inspect_local_audit_events(
                receipt_id=event["artifacts"]["receipt_id"],
                lineage_id=f"local-lineage-{accepted['job_id']}",
                contribution_attribution_id=f"local-contribution-{accepted['job_id']}",
                event_type="job_executed",
            )
            after = {
                str(path.relative_to(home)): path.read_bytes()
                for path in home.rglob("*.json")
            }

            self.assertEqual(audit["total_matching"], 1)
            self.assertEqual(event["event_type"], "job_executed")
            self.assertEqual(event["creator_node_id"], "creator-local-a")
            self.assertEqual(
                event["artifacts"]["lineage_parent_refs"], ["data/prior-job.json"]
            )
            self.assertEqual(
                event["artifacts"]["contribution_attribution"]["metadata"],
                {"project": "prototype"},
            )
            self.assertEqual(
                event["artifacts"]["contribution_attribution"]["worker_node_id"],
                "worker-local-a",
            )
            self.assertEqual(event["validation_status"], "passed")
            self.assertEqual(filtered["total_matching"], 1)
            self.assertEqual(before, after)
            with self.assertRaisesRegex(RuntimeServiceError, "start_time"):
                service.inspect_local_audit_events(start_time=True)
            with self.assertRaisesRegex(RuntimeServiceError, "event_type"):
                service.inspect_local_audit_events(event_type="unknown")
            with self.assertRaisesRegex(RuntimeServiceError, "limit"):
                service.inspect_local_audit_events(limit=0)

            status_path = home / "data" / "job-status" / f"{accepted['job_id']}.json"
            status = json.loads(status_path.read_text(encoding="utf-8"))
            status["validation"]["receipt_ref"] = "../outside.json"
            status_path.write_text(json.dumps(status), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeServiceError, "job status"):
                service.inspect_local_audit_events()

    def test_endpoint_returns_events_and_clear_filter_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = NodeRuntimeService.from_home(Path(temp_dir))
            accepted = service.submit_local_job(
                {
                    "job_type": "echo",
                    "input_payload": {"payload_type": "json", "content": {}},
                    "creator_node_id": "creator-a",
                    "requested_validation_mode": "deterministic-local",
                    "schema_version": 1,
                    "lineage_parent_refs": [],
                    "attribution_metadata": {},
                }
            )

            async def fetch() -> tuple[httpx.Response, httpx.Response]:
                transport = httpx.ASGITransport(app=create_app(service))
                async with httpx.AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    return (
                        await client.get(
                            f"/api/audit-events?manifest_id={accepted['job_id']}"
                        ),
                        await client.get("/api/audit-events?start_time=2&end_time=1"),
                    )

            response, invalid = asyncio.run(fetch())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()["events"][0]["event_type"], "job_submitted"
            )
            self.assertEqual(invalid.status_code, 400)
            self.assertEqual(invalid.json()["error"]["code"], "INVALID_INPUT")
