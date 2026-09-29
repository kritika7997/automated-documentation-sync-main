from automated_documentation_sync.changes.detector import ChangeType, PolicyChange
from automated_documentation_sync.domain.clarifications import ClarificationDecision
from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.generation.renderer import render_proposal
from automated_documentation_sync.sync.change_sets import build_change_set


def make_change_set():
    change = PolicyChange(
        change_type=ChangeType.MODIFIED,
        category="threshold",
        old_value="6 hours",
        new_value="9 hours",
        source_locations=(SourceLocation("source-v2", "Policy", "paragraph:1"),),
        classification=Classification.SOURCE_POLICY,
        affected_requirement_ids=("FR-027",),
    )
    clarification = ClarificationDecision(
        decision_id="CLAR-015",
        version="clarifications-v1",
        scope="Threshold",
        decision="Six hours is authoritative.",
        approval_evidence="review-record-15",
        applicable_requirements=("FR-027",),
    )
    return build_change_set(
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot={"time_zone": "Asia/Kolkata"},
        changes=(change,),
        clarification_impacts=(clarification,),
        not_found_items=("payment confirmation evidence",),
        out_of_scope_items=("policy-level exception approval",),
    )


def test_renderer_is_deterministic_and_preserves_traceability():
    change_set = make_change_set()

    first = render_proposal(change_set)
    second = render_proposal(change_set)

    assert first == second
    assert first.is_proposal is True
    assert "source-v2" in first.content
    assert "FR-027" in first.content
    assert "CLAR-015" in first.content
    assert "payment confirmation evidence" in first.content
    assert "policy-level exception approval" in first.content
    assert "Human approval is required" in first.content


def test_renderer_preserves_empty_unresolved_sections_without_invention():
    change_set = build_change_set(
        source_version_id="source-v1",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot={},
    )

    proposal = render_proposal(change_set)

    assert "No source changes." in proposal.content
    assert "## Conflicts\nNone." in proposal.content
    assert "## Not Found\nNone." in proposal.content
    assert "## Out of Scope\nNone." in proposal.content