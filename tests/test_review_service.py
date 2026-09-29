import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from threading import Barrier
from concurrent.futures import ThreadPoolExecutor

import pytest

from automated_documentation_sync.generation.artifacts import create_artifact_snapshot
from automated_documentation_sync.generation.renderer import DocumentationProposal
from automated_documentation_sync.changes.conflicts import ReviewOutcome
from automated_documentation_sync.review.evidence import ReviewDecision, ReviewEvidence
from automated_documentation_sync.review.service import ReviewService, UnauthorizedReviewerError
from automated_documentation_sync.storage.review_evidence_repository import InMemoryReviewEvidenceRepository
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


def evidence(
    artifact,
    decision=ReviewDecision.APPROVED,
    run_id="run-1",
    evidence_reference="review-record-1",
):
    return ReviewEvidence(
        run_id=run_id,
        change_set_id=artifact.change_set_id,
        reviewer_identity="reviewer-1",
        decision=decision,
        decided_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        evidence_reference=evidence_reference,
        source_version_id=artifact.source_version_id,
        clarification_version=artifact.clarification_version,
        artifact_hash=artifact.content_hash,
        rationale="Reviewed proposal.",
    )


def awaiting_review(orchestrator, change_set_id):
    orchestrator.start_run("run-1", source_version_id="source-v2")
    for state in (
        SyncState.PARSED,
        SyncState.VERSIONED,
        SyncState.CHANGE_DETECTED,
        SyncState.PROPOSED,
        SyncState.AWAITING_REVIEW,
    ):
        if state is SyncState.PROPOSED:
            orchestrator.transition("run-1", state, change_set_id=change_set_id)
        else:
            orchestrator.transition("run-1", state)


def test_review_view_displays_proposal_conflicts_dispositions_and_hash():
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    view = ReviewService(orchestrator).present("run-1", change_set, proposal, artifact)

    assert view.proposal.content == "# Review proposal"
    assert view.not_found_items == ("payment confirmation evidence",)
    assert view.out_of_scope_items == ("policy-level exception approval",)
    assert view.artifact_hash == artifact.content_hash
    assert view.source_version_id == "source-v2"


def test_present_rejects_artifact_bytes_that_do_not_match_declared_hash():
    change_set, proposal, artifact = review_material()
    tampered = replace(artifact, content=b"tampered proposal")
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)

    with pytest.raises(ValueError, match="Artifact content does not match its hash"):
        ReviewService(orchestrator).present("run-1", change_set, proposal, tampered)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_version_id", "different-source"),
        ("clarification_version", "different-clarifications"),
        ("requirements_version", "different-requirements"),
    ],
)
def test_present_rejects_proposal_with_mismatched_change_set_provenance(field, value):
    change_set, proposal, artifact = review_material()
    mismatched_proposal = replace(proposal, **{field: value})
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)

    with pytest.raises(ValueError, match="provenance"):
        ReviewService(orchestrator).present("run-1", change_set, mismatched_proposal, artifact)


def test_review_service_without_authorizer_fails_closed():
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    service = ReviewService(orchestrator)
    service.present("run-1", change_set, proposal, artifact)

    with pytest.raises(UnauthorizedReviewerError):
        service.submit("run-1", evidence(artifact), artifact=artifact)


def test_evidence_persistence_failure_does_not_approve_run():
    class FailingEvidenceRepository:
        def record_decision(self, run_id, review_evidence, transition):
            raise RuntimeError("evidence store unavailable")

        def history(self, run_id):
            return ()

    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    service = ReviewService(
        orchestrator,
        reviewer_authorizer=lambda _: True,
        evidence_repository=FailingEvidenceRepository(),
    )
    service.present("run-1", change_set, proposal, artifact)

    with pytest.raises(RuntimeError, match="evidence store unavailable"):
        service.submit(
            "run-1",
            evidence(artifact),
            artifact=artifact,
            not_found_outcomes={"payment confirmation evidence": ReviewOutcome.RETURNED},
        )

    assert orchestrator.resume("run-1").state is SyncState.AWAITING_REVIEW


def test_checkpoint_transition_failure_rolls_back_evidence():
    class FailingApprovalOrchestrator(SyncOrchestrator):
        def _approve_after_review(self, run_id, *, artifact_hash):
            raise RuntimeError("checkpoint store unavailable")

    change_set, proposal, artifact = review_material()
    orchestrator = FailingApprovalOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    repository = InMemoryReviewEvidenceRepository()
    service = ReviewService(
        orchestrator,
        reviewer_authorizer=lambda _: True,
        evidence_repository=repository,
    )
    service.present("run-1", change_set, proposal, artifact)

    with pytest.raises(RuntimeError, match="checkpoint store unavailable"):
        service.submit(
            "run-1",
            evidence(artifact),
            artifact=artifact,
            not_found_outcomes={"payment confirmation evidence": ReviewOutcome.RETURNED},
        )

    assert orchestrator.resume("run-1").state is SyncState.AWAITING_REVIEW
    assert repository.history("run-1") == ()


def test_competing_approval_submissions_record_only_one_decision():
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    repository = InMemoryReviewEvidenceRepository()
    service = ReviewService(
        orchestrator,
        reviewer_authorizer=lambda _: True,
        evidence_repository=repository,
    )
    service.present("run-1", change_set, proposal, artifact)
    barrier = Barrier(2)

    def submit_decision(reference):
        barrier.wait(timeout=5)
        try:
            return service.submit(
                "run-1",
                evidence(artifact, evidence_reference=reference),
                artifact=artifact,
                not_found_outcomes={"payment confirmation evidence": ReviewOutcome.RETURNED},
            )
        except ValueError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(submit_decision, ("review-a", "review-b")))

    assert sum(isinstance(result, ReviewEvidence) for result in results) == 1
    assert len(repository.history("run-1")) == 1
    assert orchestrator.resume("run-1").state is SyncState.APPROVED


def test_review_decision_cannot_replay_presented_artifact_on_another_run():
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    orchestrator.start_run("run-2", source_version_id="source-v2")
    for state in (
        SyncState.PARSED,
        SyncState.VERSIONED,
        SyncState.CHANGE_DETECTED,
    ):
        orchestrator.transition("run-2", state)
    orchestrator.transition("run-2", SyncState.PROPOSED, change_set_id=change_set.change_set_id)
    orchestrator.transition("run-2", SyncState.AWAITING_REVIEW)
    service = ReviewService(orchestrator, reviewer_authorizer=lambda _: True)
    service.present("run-1", change_set, proposal, artifact)
    service.present("run-2", change_set, proposal, artifact)

    with pytest.raises(ValueError, match="evidence run ID"):
        service.submit("run-2", evidence(artifact, run_id="run-1"), artifact=artifact)


def test_approval_rejects_artifact_different_from_presented_snapshot():
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    service = ReviewService(orchestrator, reviewer_authorizer=lambda _: True)
    service.present("run-1", change_set, proposal, artifact)
    changed_content = b"different but self-consistent artifact"
    changed_hash = hashlib.sha256(changed_content).hexdigest()
    forged = replace(artifact, content=changed_content, content_hash=changed_hash)

    with pytest.raises(ValueError, match="exact artifact presented"):
        service.submit(
            "run-1",
            evidence(forged),
            artifact=forged,
            not_found_outcomes={"payment confirmation evidence": ReviewOutcome.RETURNED},
        )


def test_approval_requires_authorized_reviewer_and_valid_evidence():
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    service = ReviewService(orchestrator, reviewer_authorizer=lambda _: False)
    service.present("run-1", change_set, proposal, artifact)

    with pytest.raises(UnauthorizedReviewerError):
        service.submit("run-1", evidence(artifact), artifact=artifact)

    service = ReviewService(orchestrator, reviewer_authorizer=lambda _: True)
    service.present("run-1", change_set, proposal, artifact)

    service.submit(
        "run-1",
        evidence(artifact),
        artifact=artifact,
        not_found_outcomes={"payment confirmation evidence": ReviewOutcome.RETURNED},
    )
    assert orchestrator.resume("run-1").state is SyncState.APPROVED
    assert service.evidence_for("run-1") == evidence(artifact)


def test_rejection_and_return_capture_evidence_and_reopen_proposal():
    _, _, artifact = review_material()
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    service = ReviewService(orchestrator, reviewer_authorizer=lambda _: True)
    service.present("run-1", change_set, proposal, artifact)

    service.submit(
        "run-1",
        evidence(artifact, ReviewDecision.RETURNED),
        artifact=artifact,
    )

    assert orchestrator.resume("run-1").state is SyncState.PROPOSED
    assert service.evidence_for("run-1").decision is ReviewDecision.RETURNED


def test_review_evidence_history_is_append_only_across_resubmissions():
    change_set, proposal, artifact = review_material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator, change_set.change_set_id)
    repository = InMemoryReviewEvidenceRepository()
    service = ReviewService(
        orchestrator,
        reviewer_authorizer=lambda _: True,
        evidence_repository=repository,
    )
    service.present("run-1", change_set, proposal, artifact)
    first = evidence(artifact, ReviewDecision.RETURNED, evidence_reference="review-record-1")
    service.submit("run-1", first, artifact=artifact)

    orchestrator.transition("run-1", SyncState.AWAITING_REVIEW)
    revised_content = "# Revised review proposal"
    revised_proposal = replace(
        proposal,
        content=revised_content,
        content_hash=hashlib.sha256(revised_content.encode("utf-8")).hexdigest(),
    )
    revised_artifact = create_artifact_snapshot(revised_proposal)
    resumed_service = ReviewService(
        orchestrator,
        reviewer_authorizer=lambda _: True,
        evidence_repository=repository,
    )
    resumed_service.present("run-1", change_set, revised_proposal, revised_artifact)
    second = evidence(revised_artifact, evidence_reference="review-record-2")
    resumed_service.submit(
        "run-1",
        second,
        artifact=revised_artifact,
        not_found_outcomes={"payment confirmation evidence": ReviewOutcome.RETURNED},
    )

    assert resumed_service.evidence_history_for("run-1") == (first, second)
    assert resumed_service.evidence_for("run-1") == second