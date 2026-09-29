from dataclasses import dataclass

from .detector import PolicyChange


@dataclass(frozen=True)
class ConfidenceAssessment:
    change: PolicyChange
    score: float
    threshold: float
    requires_human_review: bool
    can_finalize: bool

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("Confidence score must be between 0 and 1")
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0 and 1")
        requires_review = self.score < self.threshold
        if (
            self.requires_human_review != requires_review
            or self.can_finalize != (not requires_review)
        ):
            raise ValueError("Confidence assessment flags must match its score and threshold")


def assess_change_confidence(
    change: PolicyChange,
    *,
    score: float,
    threshold: float = 0.8,
) -> ConfidenceAssessment:
    if not 0.0 <= score <= 1.0:
        raise ValueError("Confidence score must be between 0 and 1")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Confidence threshold must be between 0 and 1")
    requires_review = score < threshold
    return ConfidenceAssessment(
        change=change,
        score=score,
        threshold=threshold,
        requires_human_review=requires_review,
        can_finalize=not requires_review,
    )


__all__ = ["ConfidenceAssessment", "assess_change_confidence"]