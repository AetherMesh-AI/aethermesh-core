import json
import tempfile
import unittest
from pathlib import Path

from aethermesh_core.local_audit_event import (
    AUDIT_EVENT_TYPES,
    LocalAuditEventError,
    append_local_audit_event,
    validate_local_audit_event,
)


class LocalAuditEventTests(unittest.TestCase):
    def test_validates_required_fields_and_allows_missing_optional_fields(self) -> None:
        event = _minimal_event()

        self.assertEqual(validate_local_audit_event(event), event)
        self.assertEqual(len(AUDIT_EVENT_TYPES), 7)
        self.assertIsNone(event["creator_node_id"])

    def test_appends_parseable_jsonl_events_with_local_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "audit" / "events.jsonl"
            first = append_local_audit_event(path, _minimal_event())
            second = append_local_audit_event(path, _referenced_event())
            parsed = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(parsed, [first, second])
        self.assertEqual(second["manifest_id"], "manifest-work-001")
        self.assertEqual(second["validation_receipt_id"], "receipt-work-001")
        self.assertEqual(second["lineage_parent_ids"], ["work-parent-001"])
        self.assertEqual(
            second["contribution_attribution_ids"], ["local-contribution-work-001"]
        )

    def test_rejects_invalid_required_fields_and_unknown_event_type(self) -> None:
        cases = [
            (
                {
                    key: value
                    for key, value in _minimal_event().items()
                    if key != "event_id"
                },
                "missing required",
            ),
            ({**_minimal_event(), "schema_version": 2}, "schema_version"),
            ({**_minimal_event(), "event_type": "unknown"}, "event_type"),
            ({**_minimal_event(), "creator_node_id": ""}, "creator_node_id"),
            ({**_minimal_event(), "unexpected": True}, "unsupported fields"),
        ]
        for event, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(LocalAuditEventError, message):
                    validate_local_audit_event(event)

    def test_rejects_invalid_optional_references(self) -> None:
        cases = [
            ({"manifest_id": ""}, "manifest_id"),
            ({"lineage_parent_ids": [""]}, "lineage_parent_ids"),
            ({"contribution_attribution_ids": "bad"}, "contribution_attribution_ids"),
            ({"related_file_paths": ["../outside.json"]}, "safe relative"),
            ({"hashes": {"": "sha256:value"}}, "hashes"),
            ({"signatures": {"receipt": ""}}, "signatures"),
        ]
        for optional_fields, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(LocalAuditEventError, message):
                    validate_local_audit_event({**_minimal_event(), **optional_fields})


def _minimal_event() -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_id": "audit-init-001",
        "timestamp": "2026-07-15T06:00:00Z",
        "event_type": "node_initialized",
        "actor_node_id": "local-node-a",
        "creator_node_id": None,
        "local_run_id": "run-001",
    }


def _referenced_event() -> dict[str, object]:
    return {
        **_minimal_event(),
        "event_id": "audit-validation-001",
        "event_type": "validation_result",
        "actor_node_id": "validator-local-a",
        "creator_node_id": "creator-local-a",
        "manifest_id": "manifest-work-001",
        "work_id": "work-001",
        "validation_receipt_id": "receipt-work-001",
        "lineage_parent_ids": ["work-parent-001"],
        "contribution_attribution_ids": ["local-contribution-work-001"],
        "related_file_paths": ["data/manifests/work-001.json"],
        "hashes": {"result_hash": "sha256:example"},
        "signatures": {"receipt_signature": "existing-local-signature"},
    }
