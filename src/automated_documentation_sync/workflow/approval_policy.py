from automated_documentation_sync.review.gates import (
    ApprovalBlockedError,
    ApprovalGateResult,
    evaluate_approval_gate,
    require_approval_allowed,
)

__all__ = [
    "ApprovalBlockedError",
    "ApprovalGateResult",
    "evaluate_approval_gate",
    "require_approval_allowed",
]