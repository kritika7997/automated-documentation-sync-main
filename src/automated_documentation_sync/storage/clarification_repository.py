from collections.abc import Iterable

from automated_documentation_sync.domain.clarifications import (
    ClarificationDecision,
    InvalidClarificationError,
)

from .repositories import DuplicateRecordError, InMemoryRepository


EXPECTED_CLARIFICATION_COUNT = 17


class ClarificationRepository:
    """Separate immutable storage for human-approved clarification authority records."""

    def __init__(self) -> None:
        self._records = InMemoryRepository[ClarificationDecision]()

    def add(self, decision: ClarificationDecision) -> None:
        self._records.add(decision.decision_id, decision)

    def get(self, decision_id: str) -> ClarificationDecision | None:
        return self._records.get(decision_id)

    def load_approved(self, decisions: Iterable[ClarificationDecision]) -> tuple[ClarificationDecision, ...]:
        loaded = tuple(decisions)
        if len(loaded) != EXPECTED_CLARIFICATION_COUNT:
            raise InvalidClarificationError(
                f"Expected {EXPECTED_CLARIFICATION_COUNT} approved clarification records"
            )
        for decision in loaded:
            self.add(decision)
        return tuple(self.get(decision.decision_id) for decision in loaded)  # type: ignore[misc]


__all__ = ["ClarificationRepository", "EXPECTED_CLARIFICATION_COUNT"]