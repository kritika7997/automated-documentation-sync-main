import pytest

from automated_documentation_sync.domain.classifications import Classification, ExplicitValue
from automated_documentation_sync.domain.identifiers import validate_requirement_identifier
from automated_documentation_sync.domain.models import RequirementLink, SourceLocation


def test_classifications_are_explicit_and_unique():
    assert len(Classification) == 6
    assert ExplicitValue.NOT_FOUND.value == "Not Found"
    assert ExplicitValue.OUT_OF_SCOPE.value == "Out of Scope"


def test_requirement_identifier_accepts_supported_prefixes():
    assert validate_requirement_identifier("FR-001") == "FR-001"
    assert validate_requirement_identifier("NFR-005") == "NFR-005"
    assert validate_requirement_identifier("BR-009") == "BR-009"


@pytest.mark.parametrize("identifier", ["FR-1", "REQ-001", "FR-0001", ""])
def test_requirement_identifier_rejects_invalid_values(identifier):
    with pytest.raises(ValueError):
        validate_requirement_identifier(identifier)


def test_requirement_link_validates_identifier_and_retains_provenance():
    location = SourceLocation("policy-v1", "Eligibility", "paragraph-1")
    link = RequirementLink("FR-003", Classification.HUMAN_APPROVED_CLARIFICATION, location)
    assert link.source_location == location
