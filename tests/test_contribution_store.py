import copy
import json
import shutil
import unittest
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterator

from aethermesh_core.contribution_store import (
    ContributionStoreError,
    LocalContributionStore,
)


class LocalContributionStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_root = Path(__file__).resolve().parents[1]
        self.record = json.loads(
            (
                self.repository_root / "examples/contributions/minimal-local-echo.json"
            ).read_text(encoding="utf-8")
        )

    def test_passed_receipt_records_one_linked_tamper_evident_entry(self) -> None:
        with self._root() as root:
            store = self._store(root)

            entry = store.record(self.record)

            self.assertEqual(entry["manifest_id"], "sha256:" + "a" * 64)
            self.assertEqual(entry["creator_node_id"], "node.local-creator")
            self.assertEqual(entry["contributor_node_id"], "node.local-worker")
            self.assertEqual(
                entry["validation_receipt_id"],
                "local-validation-receipt-local-job-echo-001",
            )
            self.assertEqual(entry["lineage"], self.record["lineage"])
            self.assertIsNone(entry["previous_entry_hash"])
            self.assertTrue(entry["entry_hash"].startswith("sha256:"))
            stored = [json.loads(line) for line in store.path.read_text().splitlines()]
            self.assertEqual(stored, [entry])

    def test_rejects_duplicate_manifest_without_appending(self) -> None:
        with self._root() as root:
            store = self._store(root)
            store.record(self.record)

            with self.assertRaisesRegex(ContributionStoreError, "already recorded"):
                store.record(self.record)

            self.assertEqual(len(store.path.read_text().splitlines()), 1)

    def test_rejects_failed_missing_mismatched_and_expired_receipts(self) -> None:
        with self._root() as root:
            failed = json.loads(
                (
                    self.repository_root
                    / "examples/contributions/failed-local-echo.json"
                ).read_text(encoding="utf-8")
            )
            self._copy_evidence(root, failed)
            with self.assertRaisesRegex(ContributionStoreError, "passed validation"):
                self._store(root).record(failed)

        with self._root() as root:
            missing = copy.deepcopy(self.record)
            missing["validation"]["validation_receipt_ref"] = "missing.json"
            missing["manifest_links"]["validation_manifest_ref"] = "missing.json"
            with self.assertRaisesRegex(ContributionStoreError, "does not exist"):
                self._store(root).record(missing)

        with self._root() as root:
            mismatched = copy.deepcopy(self.record)
            mismatched["result_hash"] = "sha256:" + "f" * 64
            with self.assertRaisesRegex(ContributionStoreError, "result_hash"):
                self._store(root).record(mismatched)

        with self._root() as root:
            expired = self._store(root, now="2026-07-14T12:00:02Z")
            with self.assertRaisesRegex(ContributionStoreError, "has expired"):
                expired.record(self.record)
            self.assertFalse(expired.path.exists())

    def test_rejects_a_tampered_existing_hash_chain(self) -> None:
        with self._root() as root:
            store = self._store(root)
            store.record(self.record)
            entry = json.loads(store.path.read_text())
            entry["creator_node_id"] = "node.tampered"
            store.path.write_text(json.dumps(entry) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ContributionStoreError, "hash chain is invalid"
            ):
                store.record(self.record)

    def test_rejects_invalid_configuration_and_malformed_store(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            LocalContributionStore(Path("."), max_receipt_age_seconds=-1)

        with self._root() as root:
            store = self._store(root)
            store.path.write_text("not-json\n", encoding="utf-8")
            with self.assertRaisesRegex(ContributionStoreError, "store is unreadable"):
                store.record(self.record)

    @contextmanager
    def _root(self) -> Iterator[Path]:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            self._copy_evidence(root, self.record)
            yield root

    def _copy_evidence(self, root: Path, record: dict[str, Any]) -> None:
        references = [
            record["validation"]["validation_receipt_ref"],
            record["manifest_links"]["work_manifest_ref"],
            record["source"]["local_source_path"] or record["source"]["artifact_ref"],
        ]
        for reference in references:
            assert isinstance(reference, str)
            target = root / reference
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.repository_root / reference, target)

    @staticmethod
    def _store(root: Path, now: str = "2026-07-13T12:00:02Z") -> LocalContributionStore:
        return LocalContributionStore(
            root,
            clock=lambda: datetime.fromisoformat(now.replace("Z", "+00:00")).astimezone(
                UTC
            ),
        )


if __name__ == "__main__":
    unittest.main()
