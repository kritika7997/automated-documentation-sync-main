import hashlib

from automated_documentation_sync.changes.conflicts import ConflictKind, ConflictRecord
from automated_documentation_sync.changes.detector import ChangeType, PolicyChange
from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.generation.artifacts import create_artifact_snapshot
from automated_documentation_sync.generation.renderer import render_proposal
from automated_documentation_sync.sync.change_sets import build_change_set


def make_change_set():
    change = PolicyChange(
        change_type=ChangeType.MODIFIED,
        category="threshold",
        old_value="6 hours",
        new_value="9 hours",
        source_locations=(SourceLocation("source-v2", "Policy", "threshold"),),
        classification=Classification.SOURCE_POLICY,
        affected_requirement_ids=("FR-027",),
    )
    conflict = ConflictRecord(
        conflict_id="conflict-1",
        kind=ConflictKind.THRESHOLD,
        values=("6 hours", "9 hours"),
        source_locations=(SourceLocation("source-v2", "Policy", "threshold"),),
        classifications=(Classification.SOURCE_POLICY,),
    )
    return build_change_set(
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot={"time_zone": "Asia/Kolkata"},
        changes=(change,),
        conflicts=(conflict,),
        not_found_items=("payment confirmation evidence",),
        out_of_scope_items=("policy-level exception approval",),
    )


def test_rendering_is_deterministic_and_contains_traceability_and_unresolved_items():
    first = render_proposal(make_change_set())
    second = render_proposal(make_change_set())

    assert first == second
    assert "source-v2" in first.content
    assert "FR-027" in first.content
    assert "conflict-1" in first.content
    assert "payment confirmation evidence" in first.content
    assert "policy-level exception approval" in first.content


def test_artifact_hash_is_deterministic_and_matches_rendered_bytes():
    proposal = render_proposal(make_change_set())
    artifact = create_artifact_snapshot(proposal)

    assert artifact.content_hash == hashlib.sha256(artifact.content).hexdigest()
    assert artifact.change_set_id == proposal.change_set_id
    assert artifact.source_version_id == proposal.source_version_id
    assert artifact.clarification_version == proposal.clarification_version
