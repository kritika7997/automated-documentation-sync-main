import pytest

from automated_documentation_sync.changes.conflicts import ConflictKind, ConflictRecord
from automated_documentation_sync.changes.detector import ChangeType, PolicyChange
from automated_documentation_sync.domain.clarifications import ClarificationDecision
from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.sync.change_sets import ChangeSetError, build_change_set
from automated_documentation_sync.sync.synchronizer import Synchronizer


def source_change() -> PolicyChange:
    return PolicyChange(
        change_type=ChangeType.MODIFIED,
        category="threshold",
        old_value="6 hours",
        new_value="9 hours",
        source_locations=(SourceLocation("source-v2", "Policy", "paragraph:1"),),
        classification=Classification.SOURCE_POLICY,
        affected_requirement_ids=("FR-027", "FR-028"),
    )


def clarification() -> ClarificationDecision:
    return ClarificationDecision(
        decision_id="CLAR-015",
        version="clarifications-v1",
        scope="Non-working-day threshold",
        decision="The six-hour threshold is authoritative.",
        approval_evidence="review-record-15",
        applicable_requirements=("FR-027",),
    )


def test_change_set_preserves_provenance_impacts_conflicts_and_dispositions():
    conflict = ConflictRecord(
        conflict_id="conflict-1",
        kind=ConflictKind.THRESHOLD,
        values=("6 hours", "9 hours"),
        source_locations=(SourceLocation("source-v2", "Policy", "paragraph:1"),),
        classifications=(Classification.SOURCE_POLICY,),
    )

    change_set = build_change_set(
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot={"calendar_reference": "project-calendar", "time_zone": "Asia/Kolkata"},
        changes=(source_change(),),
        clarification_impacts=(clarification(),),
        conflicts=(conflict,),
        not_found_items=("payment confirmation evidence",),
        out_of_scope_items=("policy-level exception approval",),
    )

    assert change_set.is_proposal is True
    assert change_set.source_version_id == "source-v2"
    assert change_set.changes[0].source_locations[0].document_version_id == "source-v2"
    assert change_set.conflicts == (conflict,)
    assert change_set.not_found_items == ("payment confirmation evidence",)
    assert change_set.out_of_scope_items == ("policy-level exception approval",)
    assert change_set.clarification_precedence("FR-027") == (clarification(),)


def test_change_set_identity_is_reproducible_from_all_inputs():
    values = {
        "calendar_reference": "project-calendar",
        "time_zone": "Asia/Kolkata",
    }
    first = Synchronizer().propose(
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot=values,
        changes=(source_change(),),
        clarification_impacts=(clarification(),),
    )
    second = Synchronizer().propose(
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot=dict(reversed(tuple(values.items()))),
        changes=(source_change(),),
        clarification_impacts=(clarification(),),
    )

    assert first.change_set_id == second.change_set_id


def test_change_set_requires_all_provenance_versions():
    with pytest.raises(ChangeSetError):
        build_change_set(
            source_version_id="",
            clarification_version="clarifications-v1",
            requirements_version="requirements-v1",
            configuration_snapshot={},
        )