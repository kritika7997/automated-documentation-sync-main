import hashlib
from datetime import datetime, timezone

import pytest

from automated_documentation_sync.changes.conflicts import ConflictKind, ConflictRecord, ReviewOutcome
from automated_documentation_sync.generation.artifacts import create_artifact_snapshot
from automated_documentation_sync.generation.renderer import DocumentationProposal
from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.ingestion.validation import validate_document_for_sync
from automated_documentation_sync.review.evidence import ReviewDecision, ReviewEvidence
from automated_documentation_sync.review.gates import ApprovalBlockedError
from automated_documentation_sync.review.service import ReviewService
from automated_documentation_sync.sync.change_sets import build_change_set
from automated_documentation_sync.validation.configuration import validate_project_configuration
from automated_documentation_sync.validation.required_inputs import validate_required_inputs
from automated_documentation_sync.workflow.orchestrator import SyncOrchestrator
from automated_documentation_sync.workflow.sync_states import SyncState

from tests.fakes import FakePublicationRepository


def proposal_material(*, conflict: ConflictRecord | None = None, not_found: tuple[str, ...] = ()):
    change_set = build_change_set(
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot={"time_zone": "Asia/Kolkata", "working_hours": 8},
        conflicts=(conflict,) if conflict else (),
        not_found_items=not_found,
    )
    content = "# End-to-end proposal"
    proposal = DocumentationProposal(
        change_set_id=change_set.change_set_id,
        source_version_id=change_set.source_version_id,
        clarification_version=change_set.clarification_version,
        requirements_version=change_set.requirements_version,
        content=content,
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
    )
    return change_set, proposal, create_artifact_snapshot(proposal)


def advance_to_review(orchestrator: SyncOrchestrator) -> None:
    orchestrator.start_run("e2e-run", source_version_id="source-v2")
    for state in (
        SyncState.PARSED,
        SyncState.VERSIONED,
        SyncState.CHANGE_DETECTED,
        SyncState.PROPOSED,
        SyncState.AWAITING_REVIEW,
    ):
        orchestrator.transition("e2e-run", state)


def evidence(artifact, decision: ReviewDecision = ReviewDecision.APPROVED) -> ReviewEvidence:
    return ReviewEvidence(
        reviewer_identity="e2e-reviewer",
        decision=decision,
        decided_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        evidence_reference="e2e-review-record",
        source_version_id=artifact.source_version_id,
        clarification_version=artifact.clarification_version,
        artifact_hash=artifact.content_hash,
    )


def test_happy_path_reaches_published_only_after_review_and_fake_publication():
    change_set, proposal, artifact = proposal_material(not_found=("payment confirmation evidence",))
    orchestrator = SyncOrchestrator()
    advance_to_review(orchestrator)
    review = ReviewService(orchestrator)
    review.present(change_set, proposal, artifact)
    review.submit(
        "e2e-run",
        evidence(artifact),
        reviewer_authorized=True,
        artifact=artifact,
        not_found_outcomes={"payment confirmation evidence": ReviewOutcome.RETURNED},
    )

    publication = FakePublicationRepository()
    publication.publish(approved=True, artifact_id=artifact.artifact_id, content_hash=artifact.content_hash)
    orchestrator._publish_after_confirmation("e2e-run", artifact_hash=artifact.content_hash)

    assert orchestrator.resume("e2e-run").state is SyncState.PUBLISHED
    assert publication.published[artifact.artifact_id] == artifact.content_hash


def test_empty_policy_and_missing_inputs_fail_closed():
    document = RepositoryDocument(
        content=b"",
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha="empty-v1",
        media_type="text/html",
    )
    validation = validate_document_for_sync(document, run_id="empty-e2e")
    missing_inputs = validate_required_inputs({"associate_identifier": "associate-1"})

    assert validation.checkpoint.state == "SYNC_FAILED"
    assert validation.documentation_update_allowed is False
    assert missing_inputs.is_valid is False
    assert "project_code" in missing_inputs.not_found_fields


def test_conflict_blocks_approval_and_publication_failure_does_not_publish():
    conflict = ConflictRecord(
        conflict_id="e2e-conflict",
        kind=ConflictKind.THRESHOLD,
        values=("6 hours", "9 hours"),
        source_locations=(),
        classifications=(),
    )
    change_set, proposal, artifact = proposal_material(conflict=conflict)
    orchestrator = SyncOrchestrator()
    advance_to_review(orchestrator)
    review = ReviewService(orchestrator)
    review.present(change_set, proposal, artifact)

    with pytest.raises(ApprovalBlockedError):
        review.submit("e2e-run", evidence(artifact), reviewer_authorized=True, artifact=artifact)

    publication = FakePublicationRepository()
    with pytest.raises(PermissionError):
        publication.publish(approved=False, artifact_id=artifact.artifact_id, content_hash=artifact.content_hash)
    assert publication.published == {}
    assert orchestrator.resume("e2e-run").state is SyncState.AWAITING_REVIEW


def test_configuration_and_partial_run_recovery_remain_provider_neutral():
    assert validate_project_configuration(
        {
            "week_start_day": "Monday",
            "time_zone": "Asia/Kolkata",
            "working_hours": 8,
            "calendar_reference": "project-calendar",
        }
    ).working_hours == 8

    orchestrator = SyncOrchestrator()
    orchestrator.start_run("partial-run", source_version_id="source-v1")
    orchestrator.transition("partial-run", SyncState.PARSED)
    orchestrator.transition("partial-run", SyncState.FAILED)
    resumed = SyncOrchestrator(orchestrator.repository).resume("partial-run")

    assert resumed.state is SyncState.FAILED
    assert resumed.source_version_id == "source-v1"