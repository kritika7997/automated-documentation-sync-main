import pytest

from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.sync.requirements_catalog import (
    RequirementsCatalog,
    RequirementsCatalogError,
    parse_requirements,
)


REQUIREMENTS = """
- **FR-001** (System Decision): Capture approved request fields.
- **FR-003** (Human-Approved Clarification): Eligibility requires advance approval.
- **NFR-001** (System Decision): Preserve captured inputs.
"""


def test_stable_ids_and_primary_classifications_are_preserved():
    records = parse_requirements(REQUIREMENTS, document_version_id="requirements-v1")
    catalog = RequirementsCatalog(records)

    assert [record.requirement_id for record in catalog.all()] == ["FR-001", "FR-003", "NFR-001"]
    assert catalog.get("FR-003").classification is Classification.HUMAN_APPROVED_CLARIFICATION


def test_source_statement_linkage_preserves_requirement_classification_and_location():
    catalog = RequirementsCatalog(parse_requirements(REQUIREMENTS, document_version_id="requirements-v1"))
    location = SourceLocation("source-v2", "Wage", "paragraph:1")

    catalog.add_source_link("FR-001", location)

    link = catalog.source_links("FR-001")[0]
    assert link.requirement_id == "FR-001"
    assert link.requirement_classification is Classification.SYSTEM_DECISION
    assert link.source_location == location


def test_invalid_or_duplicate_requirement_ids_are_rejected():
    with pytest.raises(RequirementsCatalogError):
        parse_requirements(
            REQUIREMENTS + "- **FR-001** (System Decision): Duplicate.\n",
            document_version_id="requirements-v1",
        )

    with pytest.raises(RequirementsCatalogError):
        parse_requirements(
            "- **FR-001** (Invented Classification): Invalid.\n",
            document_version_id="requirements-v1",
        )