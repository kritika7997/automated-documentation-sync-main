from dataclasses import dataclass

from .classifications import Classification
from .identifiers import validate_requirement_identifier


@dataclass(frozen=True)
class SourceLocation:
    document_version_id: str
    section: str
    locator: str


@dataclass(frozen=True)
class RequirementLink:
    requirement_id: str
    classification: Classification
    source_location: SourceLocation | None = None

    def __post_init__(self) -> None:
        validate_requirement_identifier(self.requirement_id)
