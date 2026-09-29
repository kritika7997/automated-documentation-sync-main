from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Protocol

from automated_documentation_sync.review.evidence import ReviewEvidence


class ReviewEvidenceRepository(Protocol):
    def record_decision(
        self,
        run_id: str,
        evidence: ReviewEvidence,
        transition: Callable[[], object],
    ) -> None:
        """Atomically persist a decision and apply its workflow transition."""

    def history(self, run_id: str) -> tuple[ReviewEvidence, ...]:
        """Return the immutable decision history for a run."""


class InMemoryReviewEvidenceRepository:
    """Process-local adapter used until the approved persistent store is selected."""

    def __init__(self) -> None:
        self._history: dict[str, list[ReviewEvidence]] = {}
        self._lock = RLock()

    def record_decision(
        self,
        run_id: str,
        evidence: ReviewEvidence,
        transition: Callable[[], object],
    ) -> None:
        if evidence.run_id != run_id:
            raise ValueError("Review evidence run ID does not match the repository key")
        with self._lock:
            history = self._history.setdefault(run_id, [])
            history.append(evidence)
            try:
                transition()
            except BaseException:
                history.pop()
                if not history:
                    del self._history[run_id]
                raise

    def history(self, run_id: str) -> tuple[ReviewEvidence, ...]:
        with self._lock:
            return tuple(self._history.get(run_id, ()))


__all__ = ["InMemoryReviewEvidenceRepository", "ReviewEvidenceRepository"]