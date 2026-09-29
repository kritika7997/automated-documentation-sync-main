from __future__ import annotations

from dataclasses import dataclass

from automated_documentation_sync.generation.artifacts import ArtifactSnapshot
from automated_documentation_sync.generation.renderer import DocumentationProposal
from automated_documentation_sync.changes.confidence import ConfidenceAssessment
from automated_documentation_sync.sync.change_sets import ChangeSet
from automated_documentation_sync.workflow.orchestrator import SyncOrchestrator
from automated_documentation_sync.workflow.sync_states import SyncState

from .evidence import ReviewDecision, ReviewEvidence
from .gates import evaluate_approval_gate, require_approval_allowed


class UnauthorizedReviewerError(PermissionError):
    """Raised when the supplied reviewer authorization is not valid."""


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
    def __init__(self, orchestrator: SyncOrchestrator) -> None:
        self.orchestrator = orchestrator
        self._evidence: dict[str, ReviewEvidence] = {}
        self._change_sets: dict[str, ChangeSet] = {}

    def present(
        self,
        change_set: ChangeSet,
        proposal: DocumentationProposal,
        artifact: ArtifactSnapshot,
    ) -> ReviewView:
        if proposal.change_set_id != change_set.change_set_id or artifact.change_set_id != change_set.change_set_id:
            raise ValueError("Proposal, artifact, and change set identifiers must match")
        if artifact.content_hash != proposal.content_hash:
            raise ValueError("Artifact hash does not match proposal content")
        self._change_sets[change_set.change_set_id] = change_set
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
        reviewer_authorized: bool,
        artifact: ArtifactSnapshot,
        confidence_assessments: tuple[ConfidenceAssessment, ...] = (),
        not_found_outcomes: dict[str, object] | None = None,
    ) -> ReviewEvidence:
        if not reviewer_authorized:
            raise UnauthorizedReviewerError(evidence.reviewer_identity)
        if evidence.artifact_hash != artifact.content_hash:
            raise ValueError("Review artifact hash does not match snapshot")
        if evidence.source_version_id != artifact.source_version_id:
            raise ValueError("Review source version does not match snapshot")
        if evidence.clarification_version != artifact.clarification_version:
            raise ValueError("Review clarification version does not match snapshot")
        change_set = self._change_sets.get(artifact.change_set_id)
        if evidence.decision is ReviewDecision.APPROVED:
            if change_set is None:
                raise ValueError("Change set must be presented before approval")
            gate = evaluate_approval_gate(
                change_set,
                confidence_assessments=confidence_assessments,
                not_found_outcomes=not_found_outcomes,
            )
            require_approval_allowed(gate)
        checkpoint = self.orchestrator.resume(run_id)
        if checkpoint.state is not SyncState.AWAITING_REVIEW:
            raise ValueError("Review evidence requires SYNC_AWAITING_REVIEW")
        target = SyncState.APPROVED if evidence.decision is ReviewDecision.APPROVED else SyncState.PROPOSED
        if target is SyncState.APPROVED:
            self.orchestrator._approve_after_review(run_id, artifact_hash=artifact.content_hash)
        else:
            self.orchestrator.transition(run_id, target, artifact_hash=artifact.content_hash)
        self._evidence[run_id] = evidence
        return evidence

    def evidence_for(self, run_id: str) -> ReviewEvidence | None:
        return self._evidence.get(run_id)


__all__ = ["ReviewService", "ReviewView", "UnauthorizedReviewerError"]