import hashlib
from datetime import datetime, timezone

import pytest

from automated_documentation_sync.generation.artifacts import create_artifact_snapshot
from automated_documentation_sync.generation.renderer import DocumentationProposal
from automated_documentation_sync.changes.conflicts import ReviewOutcome
from automated_documentation_sync.review.evidence import ReviewDecision, ReviewEvidence
from automated_documentation_sync.review.service import ReviewService, UnauthorizedReviewerError
from automated_documentation_sync.sync.change_sets import build_change_set
from automated_documentation_sync.workflow.orchestrator import SyncOrchestrator
from automated_documentation_sync.workflow.sync_states import SyncState


def review_material():
    change_set = build_change_set(
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot={"time_zone": "Asia/Kolkata"},
        conflicts=(),
        not_found_items=("payment confirmation evidence",),
        out_of_scope_items=("policy-level exception approval",),
    )
    proposal = DocumentationProposal(
        change_set_id=change_set.change_set_id,
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        content="# Review proposal",
        content_hash=hashlib.sha256(b"# Review proposal").hexdigest(),
    )
    artifact = create_artifact_snapshot(proposal)
    return change_set, proposal, artifact


def evidence(artifact, decision=ReviewDecision.APPROVED):
    return ReviewEvidence(
        reviewer_identity="reviewer-1",
        decision=decision,
        decided_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        evidence_reference="review-record-1",
        source_version_id=artifact.source_version_id,
        clarification_version=artifact.clarification_version,
        artifact_hash=artifact.content_hash,
        rationale="Reviewed proposal.",
    )


def awaiting_review(orchestrator):
    orchestrator.start_run("run-1", source_version_id="source-v2")
    for state in (
        SyncState.PARSED,
        SyncState.VERSIONED,
        SyncState.CHANGE_DETECTED,
        SyncState.PROPOSED,
        SyncState.AWAITING_REVIEW,
    ):
        orchestrator.transition("run-1", state)


def test_review_view_displays_proposal_conflicts_dispositions_and_hash():
    change_set, proposal, artifact = review_material()
    view = ReviewService(SyncOrchestrator()).present(change_set, proposal, artifact)

    assert view.proposal.content == "# Review proposal"
    assert view.not_found_items == ("payment confirmation evidence",)
    assert view.out_of_scope_items == ("policy-level exception approval",)
    assert view.artifact_hash == artifact.content_hash
    assert view.source_version_id == "source-v2"


def test_approval_requires_authorized_reviewer_and_valid_evidence():
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator)
    service = ReviewService(orchestrator)
    service.present(change_set, proposal, artifact)

    with pytest.raises(UnauthorizedReviewerError):
        service.submit("run-1", evidence(artifact), reviewer_authorized=False, artifact=artifact)

    service.submit(
        "run-1",
        evidence(artifact),
        reviewer_authorized=True,
        artifact=artifact,
        not_found_outcomes={"payment confirmation evidence": ReviewOutcome.RETURNED},
    )
    assert orchestrator.resume("run-1").state is SyncState.APPROVED
    assert service.evidence_for("run-1") == evidence(artifact)


def test_rejection_and_return_capture_evidence_and_reopen_proposal():
    _, _, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator)
    service = ReviewService(orchestrator)

    service.submit(
        "run-1",
        evidence(artifact, ReviewDecision.RETURNED),
        reviewer_authorized=True,
        artifact=artifact,
    )

    assert orchestrator.resume("run-1").state is SyncState.PROPOSED
    assert service.evidence_for("run-1").decision is ReviewDecision.RETURNED