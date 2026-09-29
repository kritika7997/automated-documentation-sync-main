import re


_IDENTIFIER_PATTERN = re.compile(r"^(FR|NFR|BR)-[0-9]{3}$")


def validate_requirement_identifier(identifier: str) -> str:
    if not isinstance(identifier, str) or _IDENTIFIER_PATTERN.fullmatch(identifier) is None:
        raise ValueError("Requirement identifier must match FR-XXX, NFR-XXX, or BR-XXX")
    return identifier
