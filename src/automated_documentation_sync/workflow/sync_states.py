from enum import StrEnum


class SyncState(StrEnum):
    INGESTED = "SYNC_INGESTED"
    PARSED = "SYNC_PARSED"
    VERSIONED = "SYNC_VERSIONED"
    CHANGE_DETECTED = "SYNC_CHANGE_DETECTED"
    PROPOSED = "SYNC_PROPOSED"
    AWAITING_REVIEW = "SYNC_AWAITING_REVIEW"
    APPROVED = "SYNC_APPROVED"
    PUBLISHED = "SYNC_PUBLISHED"
    FAILED = "SYNC_FAILED"


class InvalidSyncTransitionError(ValueError):
    """Raised when a synchronization run attempts an unsupported transition."""


_TRANSITIONS: dict[SyncState, frozenset[SyncState]] = {
    SyncState.INGESTED: frozenset({SyncState.PARSED, SyncState.FAILED}),
    SyncState.PARSED: frozenset({SyncState.VERSIONED, SyncState.FAILED}),
    SyncState.VERSIONED: frozenset({SyncState.CHANGE_DETECTED, SyncState.FAILED}),
    SyncState.CHANGE_DETECTED: frozenset({SyncState.PROPOSED, SyncState.FAILED}),
    SyncState.PROPOSED: frozenset({SyncState.AWAITING_REVIEW, SyncState.FAILED}),
    SyncState.AWAITING_REVIEW: frozenset({SyncState.PROPOSED, SyncState.APPROVED, SyncState.FAILED}),
    SyncState.APPROVED: frozenset({SyncState.PUBLISHED, SyncState.FAILED}),
    SyncState.PUBLISHED: frozenset(),
    SyncState.FAILED: frozenset(),
}


def validate_transition(current: SyncState, target: SyncState) -> None:
    if target not in _TRANSITIONS[current]:
        raise InvalidSyncTransitionError(f"Cannot transition from {current.value} to {target.value}")


def is_sync_state(value: str) -> bool:
    return value in {state.value for state in SyncState}


__all__ = ["InvalidSyncTransitionError", "SyncState", "is_sync_state", "validate_transition"]