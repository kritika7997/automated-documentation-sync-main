from __future__ import annotations

from dataclasses import dataclass

from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.identifiers import validate_requirement_identifier
from automated_documentation_sync.domain.models import SourceLocation


@dataclass(frozen=True)
class SourceRequirementLink:
    requirement_id: str
    requirement_classification: Classification
    source_location: SourceLocation

    def __post_init__(self) -> None:
        validate_requirement_identifier(self.requirement_id)


__all__ = ["SourceRequirementLink"]