import hashlib
from datetime import datetime, timezone

import pytest

from automated_documentation_sync.changes.conflicts import ConflictKind, ConflictRecord
from automated_documentation_sync.generation.artifacts import create_artifact_snapshot
from automated_documentation_sync.generation.renderer import DocumentationProposal
from automated_documentation_sync.review.evidence import ReviewDecision, ReviewEvidence
from automated_documentation_sync.review.gates import ApprovalBlockedError
from automated_documentation_sync.review.service import ReviewService
from automated_documentation_sync.sync.change_sets import build_change_set
from automated_documentation_sync.workflow.orchestrator import DuplicateRunError, SyncOrchestrator
from automated_documentation_sync.workflow.sync_states import SyncState

from tests.fakes import FakePublicationRepository


def material(*, conflict: ConflictRecord | None = None, not_found: tuple[str, ...] = ()):
    change_set = build_change_set(
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        configuration_snapshot={"time_zone": "Asia/Kolkata"},
        conflicts=(conflict,) if conflict else (),
        not_found_items=not_found,
    )
    content = "# Proposal"
    proposal = DocumentationProposal(
        change_set_id=change_set.change_set_id,
        source_version_id=change_set.source_version_id,
        clarification_version=change_set.clarification_version,
        requirements_version=change_set.requirements_version,
        content=content,
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
    )
    return change_set, proposal, create_artifact_snapshot(proposal)


def evidence(artifact: object, decision: ReviewDecision = ReviewDecision.APPROVED) -> ReviewEvidence:
    return ReviewEvidence(
        reviewer_identity="reviewer-1",
        decision=decision,
        decided_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        evidence_reference="review-record-1",
        source_version_id=artifact.source_version_id,
        clarification_version=artifact.clarification_version,
        artifact_hash=artifact.content_hash,
    )


def awaiting_review(orchestrator: SyncOrchestrator, run_id: str = "run-1") -> None:
    orchestrator.start_run(run_id, source_version_id="source-v2")
    for state in (
        SyncState.PARSED,
        SyncState.VERSIONED,
        SyncState.CHANGE_DETECTED,
        SyncState.PROPOSED,
        SyncState.AWAITING_REVIEW,
    ):
        orchestrator.transition(run_id, state)


def test_approval_bypass_and_invalid_hash_are_denied():
    change_set, proposal, artifact = material()
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator)
    service = ReviewService(orchestrator)
    service.present(change_set, proposal, artifact)

    with pytest.raises(PermissionError):
        service.submit("run-1", evidence(artifact), reviewer_authorized=False, artifact=artifact)

    invalid = ReviewEvidence(
        reviewer_identity="reviewer-1",
        decision=ReviewDecision.APPROVED,
        decided_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        evidence_reference="review-record-1",
        source_version_id=artifact.source_version_id,
        clarification_version=artifact.clarification_version,
        artifact_hash="wrong-hash",
    )
    with pytest.raises(ValueError, match="artifact hash"):
        service.submit("run-1", invalid, reviewer_authorized=True, artifact=artifact)


def test_unresolved_change_blocks_workflow_approval():
    conflict = ConflictRecord(
        conflict_id="conflict-1",
        kind=ConflictKind.THRESHOLD,
        values=("6 hours", "9 hours"),
        source_locations=(),
        classifications=(),
    )
    change_set, proposal, artifact = material(conflict=conflict, not_found=("payment evidence",))
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator)
    service = ReviewService(orchestrator)
    service.present(change_set, proposal, artifact)

    with pytest.raises(ApprovalBlockedError):
        service.submit("run-1", evidence(artifact), reviewer_authorized=True, artifact=artifact)
    assert orchestrator.resume("run-1").state is SyncState.AWAITING_REVIEW


def test_resume_and_duplicate_run_protection_work_across_orchestrator_instances():
    orchestrator = SyncOrchestrator()
    awaiting_review(orchestrator)
    resumed = SyncOrchestrator(orchestrator.repository).resume("run-1")

    assert resumed.state is SyncState.AWAITING_REVIEW
    with pytest.raises(DuplicateRunError):
        orchestrator.start_run("run-1")


def test_fake_publication_rejects_unapproved_and_duplicate_artifacts():
    _, _, artifact = material()
    repository = FakePublicationRepository()

    with pytest.raises(PermissionError):
        repository.publish(approved=False, artifact_id=artifact.artifact_id, content_hash=artifact.content_hash)
    repository.publish(approved=True, artifact_id=artifact.artifact_id, content_hash=artifact.content_hash)
    with pytest.raises(ValueError, match="Duplicate"):
        repository.publish(approved=True, artifact_id=artifact.artifact_id, content_hash=artifact.content_hash)

    assert repository.published == {artifact.artifact_id: artifact.content_hash}


def test_sync_and_overtime_status_namespaces_remain_separate_and_audit_fields_are_complete():
    orchestrator = SyncOrchestrator()
    checkpoint = orchestrator.start_run("audit-run", source_version_id="source-v2")

    audit_event = {
        "run_id": checkpoint.run_id,
        "state": checkpoint.state.value,
        "source_version_id": checkpoint.source_version_id,
        "actor": "sync-service",
        "timestamp": datetime(2026, 9, 15, tzinfo=timezone.utc),
    }

    assert audit_event["state"].startswith("SYNC_")
    assert audit_event["source_version_id"] == "source-v2"
    assert audit_event["actor"]
    assert audit_event["timestamp"].tzinfo is not None