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
- **BR-001** (Source Policy): The policy covers production associates.
"""


def test_catalog_parses_stable_ids_classifications_and_source_locations():
    records = parse_requirements(REQUIREMENTS, document_version_id="requirements-v1")

    assert [record.requirement_id for record in records] == ["FR-001", "FR-003", "NFR-001", "BR-001"]
    assert records[1].classification is Classification.HUMAN_APPROVED_CLARIFICATION
    assert records[0].source_location.document_version_id == "requirements-v1"
    assert records[0].source_location.locator == "line:2"


def test_catalog_rejects_duplicate_ids_and_unknown_classifications():
    duplicate = REQUIREMENTS + "- **FR-001** (System Decision): Duplicate.\n"
    with pytest.raises(RequirementsCatalogError):
        parse_requirements(duplicate, document_version_id="requirements-v1")

    with pytest.raises(RequirementsCatalogError):
        parse_requirements("- **FR-001** (Invented): Invalid.\n", document_version_id="requirements-v1")


def test_catalog_persists_source_statement_links_with_primary_classification():
    catalog = RequirementsCatalog(parse_requirements(REQUIREMENTS, document_version_id="requirements-v1"))
    source_location = SourceLocation("policy-v2", "Wage", "paragraph:1")

    catalog.add_source_link("FR-001", source_location)
    catalog.add_source_link("FR-001", source_location)

    links = catalog.source_links("FR-001")
    assert len(links) == 1
    assert links[0].requirement_id == "FR-001"
    assert links[0].requirement_classification is Classification.SYSTEM_DECISION
    assert links[0].source_location == source_location


def test_catalog_rejects_unknown_source_link_target():
    catalog = RequirementsCatalog(parse_requirements(REQUIREMENTS, document_version_id="requirements-v1"))

    with pytest.raises(RequirementsCatalogError):
        catalog.add_source_link("FR-999", SourceLocation("policy-v2", "Policy", "paragraph:1"))