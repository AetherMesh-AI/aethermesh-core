"""Append-only local storage for validation-gated contribution attribution."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from aethermesh_core.contribution_record import (
    ContributionRecordError,
    validate_local_contribution_record,
)


class ContributionStoreError(ValueError):
    """Raised when local contribution attribution cannot be safely recorded."""


class LocalContributionStore:
    """Store only passed, current, locally evidenced contribution records.

    Entries are JSON Lines and hash-chain to their predecessor. This is local
    audit evidence, not a consensus ledger or a reward mechanism.
    """

    def __init__(
        self,
        local_root: Path,
        *,
        max_receipt_age_seconds: int = 86_400,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        if max_receipt_age_seconds < 0:
            raise ValueError("max_receipt_age_seconds must not be negative")
        self.local_root = local_root
        self.max_receipt_age_seconds = max_receipt_age_seconds
        self.clock = clock

    @property
    def path(self) -> Path:
        return self.local_root / "contributions.jsonl"

    def record(self, document: object) -> dict[str, Any]:
        """Append one passed contribution, rejecting stale or duplicate evidence."""

        try:
            contribution = validate_local_contribution_record(document, self.local_root)
        except ContributionRecordError as exc:
            raise ContributionStoreError(str(exc)) from exc
        if contribution["validation"]["status"] != "passed":
            raise ContributionStoreError(
                "contribution requires a passed validation receipt"
            )

        receipt = self._receipt(contribution)
        if receipt["validation_status"] != "pass" or receipt["status"] != "accepted":
            raise ContributionStoreError(
                "contribution requires an accepted validation receipt"
            )
        validated_at = _timestamp(receipt["validated_at"])
        recorded_at = self.clock().astimezone(UTC)
        if (recorded_at - validated_at).total_seconds() > self.max_receipt_age_seconds:
            raise ContributionStoreError("validation receipt has expired")

        entries = self._entries()
        manifest_id = receipt["manifest_id"]
        if any(entry["manifest_id"] == manifest_id for entry in entries):
            raise ContributionStoreError("validated manifest is already recorded")
        previous_hash = entries[-1]["entry_hash"] if entries else None
        entry = {
            "recorded_at": _utc_timestamp(recorded_at),
            "manifest_id": manifest_id,
            "creator_node_id": contribution["creator_node_id"],
            "contributor_node_id": contribution["contributor_node_id"],
            "validation_receipt_id": contribution["validation_receipt_id"],
            "validator_node_id": contribution["validation"]["validator_node_id"],
            "lineage": contribution["lineage"],
            "contribution": contribution,
            "previous_entry_hash": previous_hash,
        }
        entry["entry_hash"] = _entry_hash(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(entry, sort_keys=True, separators=(",", ":")) + "\n"
            )
        return entry

    def _receipt(self, contribution: dict[str, Any]) -> dict[str, Any]:
        reference = contribution["validation"]["validation_receipt_ref"]
        assert isinstance(reference, str)
        try:
            receipt = json.loads(
                (self.local_root / reference).read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise ContributionStoreError("validation receipt is unreadable") from exc
        if not isinstance(receipt, dict):
            raise ContributionStoreError("validation receipt is malformed")
        return receipt

    def _entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        entries: list[dict[str, Any]] = []
        previous_hash: str | None = None
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
            for line in lines:
                entry = json.loads(line)
                if (
                    not isinstance(entry, dict)
                    or entry.get("previous_entry_hash") != previous_hash
                ):
                    raise ContributionStoreError(
                        "contribution store hash chain is invalid"
                    )
                entry_hash = entry.pop("entry_hash", None)
                if not isinstance(entry_hash, str) or entry_hash != _entry_hash(entry):
                    raise ContributionStoreError(
                        "contribution store hash chain is invalid"
                    )
                entry["entry_hash"] = entry_hash
                entries.append(entry)
                previous_hash = entry_hash
        except (OSError, json.JSONDecodeError) as exc:
            raise ContributionStoreError("contribution store is unreadable") from exc
        return entries


def _entry_hash(entry: dict[str, Any]) -> str:
    payload = json.dumps(entry, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ContributionStoreError("validation receipt timestamp is malformed")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError as exc:
        raise ContributionStoreError(
            "validation receipt timestamp is malformed"
        ) from exc


def _utc_timestamp(value: datetime) -> str:
    return (
        value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
