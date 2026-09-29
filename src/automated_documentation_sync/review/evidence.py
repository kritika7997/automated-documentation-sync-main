from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"


@dataclass(frozen=True)
class ReviewEvidence:
    reviewer_identity: str
    decision: ReviewDecision
    decided_at: datetime
    evidence_reference: str
    source_version_id: str
    clarification_version: str
    artifact_hash: str
    rationale: str | None = None

    def __post_init__(self) -> None:
        if not all(
            (
                self.reviewer_identity,
                self.evidence_reference,
                self.source_version_id,
                self.clarification_version,
                self.artifact_hash,
            )
        ):
            raise ValueError("Review identity, evidence, versions, and artifact hash are required")


__all__ = ["ReviewDecision", "ReviewEvidence"]