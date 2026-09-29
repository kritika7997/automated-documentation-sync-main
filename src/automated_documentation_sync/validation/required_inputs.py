from __future__ import annotations

from dataclasses import dataclass
from typing import Any


REQUIRED_CAPTURED_FIELDS = (
    "associate_identifier",
    "employment_category",
    "project_code",
    "overtime_date",
    "overtime_hours",
    "working_day_classification",
    "project_designated_working_hours",
    "wage_salary",
    "delivery_manager_or_head",
    "project_sponsor",
    "account_manager",
    "approval_evidence",
)


@dataclass(frozen=True)
class RequiredInputValidation:
    is_valid: bool
    missing_fields: tuple[str, ...]
    not_found_fields: tuple[str, ...]
    blocking_fields: tuple[str, ...]


def validate_required_inputs(values: dict[str, Any]) -> RequiredInputValidation:
    """Fail closed for defined missing inputs without fabricating undefined fields."""
    missing_fields = tuple(
        field
        for field in REQUIRED_CAPTURED_FIELDS
        if values.get(field) is None or values.get(field) == ""
    )
    return RequiredInputValidation(
        is_valid=not missing_fields,
        missing_fields=missing_fields,
        not_found_fields=missing_fields,
        blocking_fields=missing_fields,
    )


__all__ = ["REQUIRED_CAPTURED_FIELDS", "RequiredInputValidation", "validate_required_inputs"]