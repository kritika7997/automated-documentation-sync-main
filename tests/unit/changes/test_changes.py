from automated_documentation_sync.changes.confidence import assess_change_confidence
from automated_documentation_sync.changes.conflicts import ConflictKind, detect_conflicts
from automated_documentation_sync.changes.detector import ChangeType, PolicyChange, compare_policy_versions
from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.domain.policy_model import build_canonical_policy
from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser


def policy(html: str, version: str):
    document = RepositoryDocument(
        content=html.encode(),
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha=version,
        media_type="text/html",
    )
    return build_canonical_policy(PolicyParser().parse(document))


def test_semantic_changes_include_provenance_and_affected_requirements():
    previous = policy(
        "<html><body><h1>Policy</h1><p>Threshold is 6 hours.</p><p>Contact old@example.com.</p></body></html>",
        "version-1",
    )
    current = policy(
        "<html><body><h1>Policy</h1><p>Threshold is 9 hours.</p><p>Contact new@example.com.</p></body></html>",
        "version-2",
    )

    changes = compare_policy_versions(
        previous,
        current,
        affected_requirement_ids=("FR-027", "FR-035"),
    )

    assert any(change.category == "threshold" for change in changes)
    assert any(change.category == "contact" for change in changes)
    assert all(change.source_locations for change in changes)
    assert all(change.affected_requirement_ids == ("FR-027", "FR-035") for change in changes)


def test_formatting_only_changes_are_distinguished_from_semantic_changes():
    previous = policy("<html><body><h1>Policy</h1><p>Same   rule.</p></body></html>", "version-1")
    current = policy("<html><body><h1>Policy</h1><p>Same rule.</p></body></html>", "version-2")

    changes = compare_policy_versions(previous, current)

    statement_changes = [change for change in changes if change.category == "statement"]
    assert statement_changes[0].change_type is ChangeType.FORMATTING_ONLY


def test_formula_contact_and_threshold_conflicts_are_preserved_for_review():
    canonical = policy(
        "<html><body><h1>Policy</h1>"
        "<p>Hourly wage = Wage Salary / 365 / 8 hours.</p>"
        "<p>Hourly wage = Wage Salary / 365 / 9 hours.</p>"
        "<p>Threshold is 6 hours.</p><p>Threshold is 9 hours.</p>"
        "<p>Contact policy@example.com.</p><h2>FAQ</h2>"
        "<p>Where should details go? Contact faq@example.com.</p></body></html>",
        "version-1",
    )

    conflicts = detect_conflicts(canonical)

    assert {conflict.kind for conflict in conflicts} >= {
        ConflictKind.FORMULA,
        ConflictKind.THRESHOLD,
        ConflictKind.CONTACT,
    }
    assert all(conflict.requires_human_review for conflict in conflicts)


def test_low_confidence_change_requires_review_and_cannot_finalize():
    change = PolicyChange(
        change_type=ChangeType.MODIFIED,
        category="threshold",
        old_value="6 hours",
        new_value="9 hours",
        source_locations=(SourceLocation("version-2", "Policy", "threshold"),),
        classification=Classification.SOURCE_POLICY,
        affected_requirement_ids=("FR-027",),
    )

    assessment = assess_change_confidence(change, score=0.4)

    assert assessment.requires_human_review is True
    assert assessment.can_finalize is False