"""Local-first lifecycle model for one AetherMesh node runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class LocalNodeLifecycleState(StrEnum):
    """Canonical local node lifecycle states."""

    CREATED = "created"
    CONFIGURED = "configured"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    RETIRED = "retired"


class LifecycleTransitionError(ValueError):
    """Raised when a local lifecycle record or transition is invalid."""


@dataclass(frozen=True)
class LifecycleStateSpec:
    """Human-readable definition for one local lifecycle state."""

    purpose: str
    allowed_next_states: tuple[LocalNodeLifecycleState, ...]


@dataclass(frozen=True)
class LifecycleRecord:
    """Persisted lifecycle-changing event for one local node runtime.

    Each record is local-only and must carry the creator identity and active
    local manifest reference so restarts can rebuild state without relying on
    process memory, networking, token state, or dashboard state.
    """

    state: LocalNodeLifecycleState
    creator_node_id: str
    active_manifest_ref: str
    lineage_refs: tuple[str, ...] = ()
    validation_receipt_refs: tuple[str, ...] = ()
    contribution_refs: tuple[str, ...] = ()
    event: str = ""
    failure_reason: str | None = None
    failure_terminal: bool = False


LIFECYCLE_STATE_SPECS: Final[dict[LocalNodeLifecycleState, LifecycleStateSpec]] = {
    LocalNodeLifecycleState.CREATED: LifecycleStateSpec(
        purpose="A local node identity exists, but the active manifest is not ready for work.",
        allowed_next_states=(
            LocalNodeLifecycleState.CONFIGURED,
            LocalNodeLifecycleState.FAILED,
            LocalNodeLifecycleState.RETIRED,
        ),
    ),
    LocalNodeLifecycleState.CONFIGURED: LifecycleStateSpec(
        purpose="The local node references an active manifest, but validation gates have not made it runnable yet.",
        allowed_next_states=(
            LocalNodeLifecycleState.READY,
            LocalNodeLifecycleState.FAILED,
            LocalNodeLifecycleState.RETIRED,
        ),
    ),
    LocalNodeLifecycleState.READY: LifecycleStateSpec(
        purpose="Identity, active manifest, and local validation receipts permit local work to start.",
        allowed_next_states=(
            LocalNodeLifecycleState.RUNNING,
            LocalNodeLifecycleState.PAUSED,
            LocalNodeLifecycleState.FAILED,
            LocalNodeLifecycleState.RETIRED,
        ),
    ),
    LocalNodeLifecycleState.RUNNING: LifecycleStateSpec(
        purpose="The single local node runtime is actively accepting or executing local work.",
        allowed_next_states=(
            LocalNodeLifecycleState.PAUSED,
            LocalNodeLifecycleState.VALIDATING,
            LocalNodeLifecycleState.FAILED,
        ),
    ),
    LocalNodeLifecycleState.PAUSED: LifecycleStateSpec(
        purpose="The runtime stopped intentionally while preserving manifest, lineage, validation, and attribution records.",
        allowed_next_states=(
            LocalNodeLifecycleState.READY,
            LocalNodeLifecycleState.RUNNING,
            LocalNodeLifecycleState.FAILED,
            LocalNodeLifecycleState.RETIRED,
        ),
    ),
    LocalNodeLifecycleState.VALIDATING: LifecycleStateSpec(
        purpose="A work result is being checked before contribution attribution can advance.",
        allowed_next_states=(
            LocalNodeLifecycleState.RUNNING,
            LocalNodeLifecycleState.COMPLETED,
            LocalNodeLifecycleState.FAILED,
        ),
    ),
    LocalNodeLifecycleState.COMPLETED: LifecycleStateSpec(
        purpose="Local work finished with validation receipts and contribution attribution linked.",
        allowed_next_states=(
            LocalNodeLifecycleState.READY,
            LocalNodeLifecycleState.RUNNING,
            LocalNodeLifecycleState.RETIRED,
        ),
    ),
    LocalNodeLifecycleState.FAILED: LifecycleStateSpec(
        purpose="A recoverable or terminal error is visible and linked to validation evidence instead of hidden.",
        allowed_next_states=(
            LocalNodeLifecycleState.CONFIGURED,
            LocalNodeLifecycleState.READY,
            LocalNodeLifecycleState.RETIRED,
        ),
    ),
    LocalNodeLifecycleState.RETIRED: LifecycleStateSpec(
        purpose="The local runtime is intentionally inactive; persisted records remain audit evidence.",
        allowed_next_states=(),
    ),
}

_WORK_RELATED_STATES: Final[frozenset[LocalNodeLifecycleState]] = frozenset(
    {
        LocalNodeLifecycleState.RUNNING,
        LocalNodeLifecycleState.PAUSED,
        LocalNodeLifecycleState.VALIDATING,
        LocalNodeLifecycleState.COMPLETED,
        LocalNodeLifecycleState.FAILED,
    }
)
_TERMINAL_FAILURE_NEXT_STATES: Final[frozenset[LocalNodeLifecycleState]] = frozenset(
    {LocalNodeLifecycleState.RETIRED}
)


def canonical_lifecycle_states() -> tuple[LocalNodeLifecycleState, ...]:
    """Return canonical states in progression order for docs, APIs, and tests."""

    return tuple(LocalNodeLifecycleState)


def allowed_next_states(
    state: LocalNodeLifecycleState,
) -> tuple[LocalNodeLifecycleState, ...]:
    """Return allowed next states for a canonical local lifecycle state."""

    return LIFECYCLE_STATE_SPECS[state].allowed_next_states


def validate_lifecycle_record(record: LifecycleRecord) -> None:
    """Validate fields required on every lifecycle-changing persisted record."""

    if not record.creator_node_id:
        raise LifecycleTransitionError("lifecycle record requires creator_node_id")
    if not record.active_manifest_ref:
        raise LifecycleTransitionError("lifecycle record requires active_manifest_ref")
    if record.state is LocalNodeLifecycleState.FAILED and not record.failure_reason:
        raise LifecycleTransitionError(
            "failed lifecycle records require failure_reason"
        )
    if record.failure_terminal and record.state is not LocalNodeLifecycleState.FAILED:
        raise LifecycleTransitionError(
            "failure_terminal is only valid on failed records"
        )


def validate_transition(
    previous: LifecycleRecord, next_record: LifecycleRecord
) -> None:
    """Reject invalid local lifecycle transitions.

    Work-related transitions must preserve creator identity, the active manifest,
    lineage references, validation receipt references, and contribution
    attribution references. New references may be appended, but existing audit
    links may not disappear across pause, failure, validation, completion, or
    restart-derived paths.
    """

    validate_lifecycle_record(previous)
    validate_lifecycle_record(next_record)
    if (
        previous.failure_terminal
        and next_record.state not in _TERMINAL_FAILURE_NEXT_STATES
    ):
        raise LifecycleTransitionError(
            "terminal failed lifecycle records may only retire"
        )
    if next_record.state not in allowed_next_states(previous.state):
        raise LifecycleTransitionError(
            f"invalid local lifecycle transition: {previous.state.value} -> {next_record.state.value}"
        )
    if (
        previous.state in _WORK_RELATED_STATES
        or next_record.state in _WORK_RELATED_STATES
    ):
        _require_work_links_preserved(previous, next_record)


def recover_lifecycle_state(
    record: LifecycleRecord, *, runtime_active: bool
) -> LocalNodeLifecycleState:
    """Derive current state from persisted local records plus the runtime marker.

    The persisted record supplies identity, active manifest, lineage, validation,
    contribution, and failure evidence. The volatile process marker can only
    distinguish an actively running runtime from restart recovery; it cannot
    erase failure, completion, retirement, validation, or pause evidence.
    """

    validate_lifecycle_record(record)
    if record.state in {
        LocalNodeLifecycleState.RETIRED,
        LocalNodeLifecycleState.FAILED,
        LocalNodeLifecycleState.COMPLETED,
        LocalNodeLifecycleState.VALIDATING,
        LocalNodeLifecycleState.PAUSED,
    }:
        return record.state
    if runtime_active and record.state is LocalNodeLifecycleState.READY:
        return LocalNodeLifecycleState.RUNNING
    return record.state


def _require_work_links_preserved(
    previous: LifecycleRecord, next_record: LifecycleRecord
) -> None:
    if next_record.creator_node_id != previous.creator_node_id:
        raise LifecycleTransitionError("work transition must preserve creator_node_id")
    if next_record.active_manifest_ref != previous.active_manifest_ref:
        raise LifecycleTransitionError(
            "work transition must preserve active_manifest_ref"
        )
    _require_refs_preserved(
        "lineage_refs", previous.lineage_refs, next_record.lineage_refs
    )
    _require_refs_preserved(
        "validation_receipt_refs",
        previous.validation_receipt_refs,
        next_record.validation_receipt_refs,
    )
    _require_refs_preserved(
        "contribution_refs", previous.contribution_refs, next_record.contribution_refs
    )


def _require_refs_preserved(
    field_name: str, previous_refs: tuple[str, ...], next_refs: tuple[str, ...]
) -> None:
    missing = tuple(ref for ref in previous_refs if ref not in next_refs)
    if missing:
        raise LifecycleTransitionError(
            f"work transition must preserve {field_name}: {', '.join(missing)}"
        )
