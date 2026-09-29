from __future__ import annotations

from dataclasses import dataclass

from .classifications import Classification
from .identifiers import validate_requirement_identifier


class InvalidClarificationError(ValueError):
    """Raised when an approved clarification record is incomplete or invalid."""


@dataclass(frozen=True)
class ClarificationDecision:
    decision_id: str
    version: str
    scope: str
    decision: str
    approval_evidence: str
    applicable_requirements: tuple[str, ...]
    classification: Classification = Classification.HUMAN_APPROVED_CLARIFICATION

    def __post_init__(self) -> None:
        if not all((self.decision_id, self.version, self.scope, self.decision, self.approval_evidence)):
            raise InvalidClarificationError(
                "Clarification identity, version, scope, decision, and approval evidence are required"
            )
        if not self.applicable_requirements:
            raise InvalidClarificationError("At least one applicable requirement is required")
        for requirement_id in self.applicable_requirements:
            validate_requirement_identifier(requirement_id)
        if self.classification is not Classification.HUMAN_APPROVED_CLARIFICATION:
            raise InvalidClarificationError("Clarification records must retain Human-Approved Clarification classification")


__all__ = ["ClarificationDecision", "InvalidClarificationError"]