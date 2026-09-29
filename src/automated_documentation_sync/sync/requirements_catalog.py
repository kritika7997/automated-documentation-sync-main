from __future__ import annotations

import re
from dataclasses import dataclass

from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.domain.identifiers import validate_requirement_identifier


class RequirementsCatalogError(ValueError):
    """Raised when finalized requirement definitions are invalid or incomplete."""


@dataclass(frozen=True)
class RequirementRecord:
    requirement_id: str
    text: str
    classification: Classification
    source_location: SourceLocation


_REQUIREMENT_LINE = re.compile(
    r"^-\s+\*\*((?:FR|NFR|BR)-\d{3})\*\*\s+\(([^)]+)\):\s+(.+?)\s*$"
)


def _classification(value: str) -> Classification:
    try:
        return Classification(value)
    except ValueError as exc:
        raise RequirementsCatalogError(f"Unknown requirement classification: {value}") from exc


def parse_requirements(
    markdown: str,
    *,
    document_version_id: str,
) -> tuple[RequirementRecord, ...]:
    """Parse finalized requirement definition lines and retain their source locations."""
    if not markdown:
        raise RequirementsCatalogError("Requirements content is required")
    if not document_version_id:
        raise RequirementsCatalogError("Requirements document version is required")

    records: list[RequirementRecord] = []
    seen: set[str] = set()
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        match = _REQUIREMENT_LINE.match(line)
        if match is None:
            continue
        requirement_id, classification_value, text = match.groups()
        validate_requirement_identifier(requirement_id)
        if requirement_id in seen:
            raise RequirementsCatalogError(f"Duplicate requirement identifier: {requirement_id}")
        seen.add(requirement_id)
        records.append(
            RequirementRecord(
                requirement_id=requirement_id,
                text=text,
                classification=_classification(classification_value),
                source_location=SourceLocation(
                    document_version_id=document_version_id,
                    section="requirements",
                    locator=f"line:{line_number}",
                ),
            )
        )
    if not records:
        raise RequirementsCatalogError("No finalized requirement definitions were found")
    return tuple(records)


class RequirementsCatalog:
    def __init__(self, records: tuple[RequirementRecord, ...]) -> None:
        self._records = {record.requirement_id: record for record in records}
        if len(self._records) != len(records):
            raise RequirementsCatalogError("Requirement identifiers must be unique")
        self._links: dict[str, tuple[object, ...]] = {}

    def get(self, requirement_id: str) -> RequirementRecord | None:
        return self._records.get(requirement_id)

    def all(self) -> tuple[RequirementRecord, ...]:
        return tuple(self._records.values())

    def add_source_link(self, requirement_id: str, source_location: SourceLocation) -> None:
        if self.get(requirement_id) is None:
            raise RequirementsCatalogError(f"Unknown requirement identifier: {requirement_id}")
        from .traceability import SourceRequirementLink

        link = SourceRequirementLink(
            requirement_id=requirement_id,
            requirement_classification=self._records[requirement_id].classification,
            source_location=source_location,
        )
        self._links.setdefault(requirement_id, ())
        if link not in self._links[requirement_id]:
            self._links[requirement_id] += (link,)

    def source_links(self, requirement_id: str) -> tuple[object, ...]:
        if self.get(requirement_id) is None:
            raise RequirementsCatalogError(f"Unknown requirement identifier: {requirement_id}")
        return self._links.get(requirement_id, ())


__all__ = ["RequirementRecord", "RequirementsCatalog", "RequirementsCatalogError", "parse_requirements"]