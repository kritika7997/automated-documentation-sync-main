import pytest

from automated_documentation_sync.changes.confidence import assess_change_confidence
from automated_documentation_sync.changes.conflicts import ConflictKind, ConflictRecord, ReviewOutcome
from automated_documentation_sync.changes.detector import ChangeType, PolicyChange
from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.review.gates import (
    ApprovalBlockedError,
    InvalidReviewOutcomeError,
    evaluate_approval_gate,
    require_approval_allowed,
)
from automated_documentation_sync.sync.change_sets import build_change_set


def change_set(**kwargs):
    return build_change_set(
        source_version_id="source-v1",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot={},
        **kwargs,
    )


def conflict(review_outcome=None):
    return ConflictRecord(
        conflict_id="conflict-1",
        kind=ConflictKind.THRESHOLD,
        values=("6 hours", "9 hours"),
        source_locations=(SourceLocation("source-v1", "Policy", "threshold"),),
        classifications=(Classification.SOURCE_POLICY,),
        review_outcome=review_outcome,
    )


def low_confidence():
    policy_change = PolicyChange(
        change_type=ChangeType.MODIFIED,
        category="threshold",
        old_value="6 hours",
        new_value="9 hours",
        source_locations=(SourceLocation("source-v1", "Policy", "threshold"),),
        classification=Classification.SOURCE_POLICY,
    )
    return assess_change_confidence(policy_change, score=0.3)


def test_unresolved_conflict_and_not_found_block_approval():
    result = evaluate_approval_gate(
        change_set(conflicts=(conflict(),), not_found_items=("payment evidence",)),
        confidence_assessments=(low_confidence(),),
    )

    assert result.can_approve is False
    assert result.unresolved_conflict_ids == ("conflict-1",)
    assert result.low_confidence_categories == ("threshold",)
    assert result.unresolved_not_found_items == ("payment evidence",)
    with pytest.raises(ApprovalBlockedError):
        require_approval_allowed(result)


def test_explicit_outcomes_allow_approval_without_silent_resolution():
    result = evaluate_approval_gate(
        change_set(
            conflicts=(conflict(ReviewOutcome.APPROVED),),
            not_found_items=("payment evidence",),
        ),
        confidence_assessments=(),
        not_found_outcomes={"payment evidence": ReviewOutcome.RETURNED},
    )

    assert result.can_approve is True
    require_approval_allowed(result)


def test_invalid_not_found_outcome_does_not_clear_the_gate():
    with pytest.raises(InvalidReviewOutcomeError):
        evaluate_approval_gate(
            change_set(not_found_items=("payment evidence",)),
            not_found_outcomes={"payment evidence": "invented-outcome"},
        )