from enum import StrEnum


class Classification(StrEnum):
    SOURCE_POLICY = "Source Policy"
    SOURCE_FAQ = "Source FAQ"
    HUMAN_APPROVED_CLARIFICATION = "Human-Approved Clarification"
    SYSTEM_DECISION = "System Decision"
    NOT_FOUND = "Not Found"
    OUT_OF_SCOPE = "Out of Scope"


class ExplicitValue(StrEnum):
    NOT_FOUND = "Not Found"
    OUT_OF_SCOPE = "Out of Scope"
