from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable

from automated_documentation_sync.generation.artifacts import ArtifactSnapshot
from automated_documentation_sync.generation.renderer import DocumentationProposal
from automated_documentation_sync.changes.confidence import ConfidenceAssessment
from automated_documentation_sync.storage.review_evidence_repository import (
    InMemoryReviewEvidenceRepository,
    ReviewEvidenceRepository,
)
from automated_documentation_sync.sync.change_sets import ChangeSet
from automated_documentation_sync.workflow.orchestrator import SyncOrchestrator
from automated_documentation_sync.workflow.sync_states import SyncState

from .evidence import ReviewDecision, ReviewEvidence
from .gates import evaluate_approval_gate, require_approval_allowed


class UnauthorizedReviewerError(PermissionError):
    """Raised when the supplied reviewer authorization is not valid."""


ReviewerAuthorizer = Callable[[ReviewEvidence], bool]


@dataclass(frozen=True)
class ReviewView:
    proposal: DocumentationProposal
    conflicts: tuple[object, ...]
    not_found_items: tuple[str, ...]
    out_of_scope_items: tuple[str, ...]
    source_version_id: str
    clarification_version: str
    artifact_hash: str


class ReviewService:
    def __init__(
        self,
        orchestrator: SyncOrchestrator,
        reviewer_authorizer: ReviewerAuthorizer | None = None,
        evidence_repository: ReviewEvidenceRepository | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self._reviewer_authorizer = reviewer_authorizer
        self._evidence_repository = evidence_repository or InMemoryReviewEvidenceRepository()
        self._change_sets_by_run: dict[str, ChangeSet] = {}
        self._artifacts_by_run: dict[str, ArtifactSnapshot] = {}

    def present(
        self,
        run_id: str,
        change_set: ChangeSet,
        proposal: DocumentationProposal,
        artifact: ArtifactSnapshot,
    ) -> ReviewView:
        checkpoint = self.orchestrator.resume(run_id)
        if checkpoint.state is not SyncState.AWAITING_REVIEW:
            raise ValueError("A run must be awaiting review before its proposal is presented")
        if checkpoint.source_version_id != change_set.source_version_id:
            raise ValueError("Change set source version does not match the run")
        if checkpoint.change_set_id != change_set.change_set_id:
            raise ValueError("Change set identifier does not match the run")
        if proposal.change_set_id != change_set.change_set_id or artifact.change_set_id != change_set.change_set_id:
            raise ValueError("Proposal, artifact, and change set identifiers must match")
        if (
            proposal.source_version_id != change_set.source_version_id
            or proposal.clarification_version != change_set.clarification_version
            or proposal.requirements_version != change_set.requirements_version
            or artifact.source_version_id != change_set.source_version_id
            or artifact.clarification_version != change_set.clarification_version
        ):
            raise ValueError("Proposal and artifact provenance must match the change set")
        proposal_content = proposal.content.encode("utf-8")
        if hashlib.sha256(proposal_content).hexdigest() != proposal.content_hash:
            raise ValueError("Proposal content does not match its hash")
        if hashlib.sha256(artifact.content).hexdigest() != artifact.content_hash:
            raise ValueError("Artifact content does not match its hash")
        if artifact.content != proposal_content:
            raise ValueError("Artifact content does not match proposal content")
        if artifact.content_hash != proposal.content_hash:
            raise ValueError("Artifact hash does not match proposal content")
        previous_artifact = self._artifacts_by_run.get(run_id)
        if previous_artifact is not None and previous_artifact != artifact:
            history = self._evidence_repository.history(run_id)
            if not history or history[-1].decision not in {
                ReviewDecision.REJECTED,
                ReviewDecision.RETURNED,
            }:
                raise ValueError("A run can revise its artifact only after a returned or rejected decision")
        self._change_sets_by_run[run_id] = change_set
        self._artifacts_by_run[run_id] = artifact
        return ReviewView(
            proposal=proposal,
            conflicts=change_set.conflicts,
            not_found_items=change_set.not_found_items,
            out_of_scope_items=change_set.out_of_scope_items,
            source_version_id=change_set.source_version_id,
            clarification_version=change_set.clarification_version,
            artifact_hash=artifact.content_hash,
        )

    def submit(
        self,
        run_id: str,
        evidence: ReviewEvidence,
        *,
        artifact: ArtifactSnapshot,
        confidence_assessments: tuple[ConfidenceAssessment, ...] = (),
        not_found_outcomes: dict[str, object] | None = None,
    ) -> ReviewEvidence:
        checkpoint = self.orchestrator.resume(run_id)
        if checkpoint.state is not SyncState.AWAITING_REVIEW:
            raise ValueError("Review evidence requires SYNC_AWAITING_REVIEW")
        if evidence.run_id != run_id:
            raise ValueError("Review evidence run ID does not match the target run")
        if evidence.change_set_id != artifact.change_set_id:
            raise ValueError("Review evidence change set does not match the artifact")
        if self._reviewer_authorizer is None or not self._reviewer_authorizer(evidence):
            raise UnauthorizedReviewerError(evidence.reviewer_identity)
        if checkpoint.source_version_id != artifact.source_version_id:
            raise ValueError("Review artifact source version does not match the run")
        if checkpoint.change_set_id != artifact.change_set_id:
            raise ValueError("Review artifact change set does not match the run")
        if self._artifacts_by_run.get(run_id) != artifact:
            raise ValueError("Review decision must reference the exact artifact presented for this run")
        if hashlib.sha256(artifact.content).hexdigest() != artifact.content_hash:
            raise ValueError("Artifact content does not match its hash")
        if evidence.artifact_hash != artifact.content_hash:
            raise ValueError("Review artifact hash does not match snapshot")
        if evidence.source_version_id != artifact.source_version_id:
            raise ValueError("Review source version does not match snapshot")
        if evidence.clarification_version != artifact.clarification_version:
            raise ValueError("Review clarification version does not match snapshot")
        change_set = self._change_sets_by_run.get(run_id)
        if evidence.decision is ReviewDecision.APPROVED:
            if change_set is None:
                raise ValueError("Change set must be presented before approval")
            gate = evaluate_approval_gate(
                change_set,
                confidence_assessments=confidence_assessments,
                not_found_outcomes=not_found_outcomes,
            )
            require_approval_allowed(gate)
        target = SyncState.APPROVED if evidence.decision is ReviewDecision.APPROVED else SyncState.PROPOSED

        def transition() -> None:
            if target is SyncState.APPROVED:
                self.orchestrator._approve_after_review(run_id, artifact_hash=artifact.content_hash)
            else:
                self.orchestrator.transition(run_id, target, artifact_hash=artifact.content_hash)

        self._evidence_repository.record_decision(run_id, evidence, transition)
        return evidence

    def evidence_for(self, run_id: str) -> ReviewEvidence | None:
        history = self._evidence_repository.history(run_id)
        return history[-1] if history else None

    def evidence_history_for(self, run_id: str) -> tuple[ReviewEvidence, ...]:
        return self._evidence_repository.history(run_id)


__all__ = ["ReviewService", "ReviewView", "ReviewerAuthorizer", "UnauthorizedReviewerError"]