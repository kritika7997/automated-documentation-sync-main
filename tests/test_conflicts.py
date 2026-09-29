from automated_documentation_sync.changes.confidence import assess_change_confidence
from automated_documentation_sync.changes.conflicts import (
    ConflictKind,
    ReviewOutcome,
    detect_conflicts,
)
from automated_documentation_sync.changes.detector import ChangeType, PolicyChange
from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.domain.policy_model import build_canonical_policy
from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser


def policy(content: str, version: str):
    document = RepositoryDocument(
        content=content.encode(),
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha=version,
        media_type="text/html",
    )
    return build_canonical_policy(PolicyParser().parse(document))


def test_formula_threshold_and_contact_conflicts_preserve_values_for_review():
    canonical = policy(
        "<html><body><h1>Policy</h1>"
        "<p>Hourly wage = Wage Salary / 365 / 8 hours.</p>"
        "<p>Hourly wage = Wage Salary / 365 / 9 hours.</p>"
        "<p>Threshold is 6 hours.</p><p>Threshold is 9 hours.</p>"
        "<p>Contact policy@example.com.</p>"
        "<h2>FAQ</h2><p>Where should details go? Contact faq@example.com.</p>"
        "</body></html>",
        "v1",
    )

    conflicts = detect_conflicts(canonical)

    kinds = {conflict.kind for conflict in conflicts}
    assert {ConflictKind.FORMULA, ConflictKind.THRESHOLD, ConflictKind.CONTACT}.issubset(kinds)
    assert all(conflict.requires_human_review for conflict in conflicts)
    formula_conflict = next(conflict for conflict in conflicts if conflict.kind is ConflictKind.FORMULA)
    assert any("8 hours" in value for value in formula_conflict.values)
    assert any("9 hours" in value for value in formula_conflict.values)


def test_faq_policy_conflict_is_retained_without_silent_resolution():
    canonical = policy(
        "<html><body><h1>Policy</h1><p>Non-working-day threshold is 6 hours.</p>"
        "<h2>FAQ</h2><p>What is the threshold? 9 hours.</p></body></html>",
        "v1",
    )

    conflicts = detect_conflicts(canonical)

    faq_conflicts = [conflict for conflict in conflicts if conflict.kind is ConflictKind.FAQ_POLICY]
    assert len(faq_conflicts) == 1
    assert faq_conflicts[0].review_outcome is None
    resolved = faq_conflicts[0].with_review_outcome(ReviewOutcome.APPROVED)
    assert resolved.is_authoritative is True
    assert resolved.is_finalizable is True


def test_low_confidence_change_is_held_for_human_review():
    change = PolicyChange(
        change_type=ChangeType.MODIFIED,
        category="threshold",
        old_value="6 hours",
        new_value="9 hours",
        source_locations=(SourceLocation("v1", "Policy", "threshold"),),
        classification=Classification.SOURCE_POLICY,
    )

    assessment = assess_change_confidence(change, score=0.4)

    assert assessment.requires_human_review is True
    assert assessment.can_finalize is False