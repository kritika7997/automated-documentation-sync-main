from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from automated_documentation_sync.changes.confidence import ConfidenceAssessment
from automated_documentation_sync.changes.conflicts import ReviewOutcome
from automated_documentation_sync.sync.change_sets import ChangeSet


@dataclass(frozen=True)
class ApprovalGateResult:
    can_approve: bool
    unresolved_conflict_ids: tuple[str, ...]
    low_confidence_categories: tuple[str, ...]
    unresolved_not_found_items: tuple[str, ...]


class ApprovalBlockedError(ValueError):
    """Raised when unresolved change evidence prevents approval."""


class InvalidReviewOutcomeError(ValueError):
    """Raised when a Not Found item receives an unsupported outcome."""


def evaluate_approval_gate(
    change_set: ChangeSet,
    *,
    confidence_assessments: tuple[ConfidenceAssessment, ...] = (),
    not_found_outcomes: Mapping[str, ReviewOutcome] | None = None,
) -> ApprovalGateResult:
    outcomes = not_found_outcomes or {}
    invalid_outcomes = tuple(
        item for item, outcome in outcomes.items() if not isinstance(outcome, ReviewOutcome)
    )
    if invalid_outcomes:
        raise InvalidReviewOutcomeError(
            f"Unsupported review outcomes for: {', '.join(invalid_outcomes)}"
        )
    unresolved_conflicts = tuple(
        conflict.conflict_id
        for conflict in change_set.conflicts
        if conflict.review_outcome is None
    )
    low_confidence = tuple(
        assessment.change.category
        for assessment in confidence_assessments
        if assessment.requires_human_review and not assessment.can_finalize
    )
    unresolved_not_found = tuple(
        item
        for item in change_set.not_found_items
        if outcomes.get(item) is None
    )
    return ApprovalGateResult(
        can_approve=not (unresolved_conflicts or low_confidence or unresolved_not_found),
        unresolved_conflict_ids=unresolved_conflicts,
        low_confidence_categories=low_confidence,
        unresolved_not_found_items=unresolved_not_found,
    )


def require_approval_allowed(result: ApprovalGateResult) -> None:
    if not result.can_approve:
        blocked = (
            result.unresolved_conflict_ids
            + result.low_confidence_categories
            + result.unresolved_not_found_items
        )
        raise ApprovalBlockedError(f"Explicit review outcomes are required: {', '.join(blocked)}")


__all__ = [
    "ApprovalBlockedError",
    "ApprovalGateResult",
    "InvalidReviewOutcomeError",
    "evaluate_approval_gate",
    "require_approval_allowed",
]