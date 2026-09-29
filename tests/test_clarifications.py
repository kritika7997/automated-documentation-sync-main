import pytest

from automated_documentation_sync.domain.clarifications import (
    ClarificationDecision,
    InvalidClarificationError,
)
from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.storage.clarification_repository import (
    ClarificationRepository,
)
from automated_documentation_sync.storage.repositories import DuplicateRecordError


def make_decision(number: int = 1) -> ClarificationDecision:
    return ClarificationDecision(
        decision_id=f"CLAR-{number:03d}",
        version="clarifications-v1",
        scope="Overtime eligibility",
        decision="Approved overtime requires advance business approval.",
        approval_evidence=f"review-record-{number}",
        applicable_requirements=("FR-003", "FR-014"),
    )


def test_clarification_identity_version_evidence_and_requirements_are_retained():
    decision = make_decision()

    assert decision.decision_id == "CLAR-001"
    assert decision.version == "clarifications-v1"
    assert decision.classification is Classification.HUMAN_APPROVED_CLARIFICATION
    assert decision.approval_evidence == "review-record-1"
    assert decision.applicable_requirements == ("FR-003", "FR-014")


def test_incomplete_clarification_is_rejected_without_inventing_evidence():
    with pytest.raises(InvalidClarificationError):
        ClarificationDecision(
            decision_id="CLAR-001",
            version="clarifications-v1",
            scope="Overtime eligibility",
            decision="Approved overtime requires advance business approval.",
            approval_evidence="",
            applicable_requirements=("FR-003",),
        )


def test_repository_loads_seventeen_records_as_separate_authority_records():
    decisions = tuple(make_decision(number) for number in range(1, 18))
    repository = ClarificationRepository()

    loaded = repository.load_approved(decisions)

    assert loaded == decisions
    assert repository.get("CLAR-017") == decisions[-1]
    assert loaded[0].classification is Classification.HUMAN_APPROVED_CLARIFICATION


def test_repository_rejects_incomplete_set_and_duplicate_identity():
    repository = ClarificationRepository()

    with pytest.raises(InvalidClarificationError):
        repository.load_approved((make_decision(),))

    repository.add(make_decision())
    with pytest.raises(DuplicateRecordError):
        repository.add(make_decision())