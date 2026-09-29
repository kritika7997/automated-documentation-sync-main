from datetime import date

from automated_documentation_sync.validation.configuration import validate_project_configuration
from automated_documentation_sync.validation.required_inputs import validate_required_inputs


def complete_configuration(working_hours: int) -> dict[str, object]:
    return {
        "week_start_day": "Monday",
        "time_zone": "Asia/Kolkata",
        "working_hours": working_hours,
        "calendar_reference": "project-calendar",
    }


def complete_inputs() -> dict[str, object]:
    return {
        "associate_identifier": "associate-1",
        "employment_category": "full-time",
        "project_code": "project-1",
        "overtime_date": date(2026, 9, 8),
        "overtime_hours": 2.5,
        "working_day_classification": "working-day",
        "project_designated_working_hours": 8,
        "wage_salary": 100000,
        "delivery_manager_or_head": "manager-1",
        "project_sponsor": "sponsor-1",
        "account_manager": "account-1",
        "approval_evidence": "approval-reference-1",
    }


def test_configuration_accepts_eight_and_nine_without_defaults():
    assert validate_project_configuration(complete_configuration(8)).working_hours == 8
    assert validate_project_configuration(complete_configuration(9)).working_hours == 9


def test_missing_configuration_and_invalid_hours_block_without_defaults():
    for values in (
        {},
        {"week_start_day": "Monday", "time_zone": "Asia/Kolkata", "working_hours": 8},
        complete_configuration(7),
        complete_configuration(10),
    ):
        try:
            validate_project_configuration(values)
        except ValueError:
            continue
        raise AssertionError("Invalid or missing configuration must block")


def test_missing_required_inputs_are_not_found_and_block_processing():
    values = complete_inputs()
    values.pop("approval_evidence")
    values.pop("project_code")

    result = validate_required_inputs(values)

    assert result.is_valid is False
    assert result.missing_fields == ("project_code", "approval_evidence")
    assert result.not_found_fields == result.missing_fields
    assert result.blocking_fields == result.missing_fields


def test_complete_required_inputs_pass_and_undefined_fields_are_not_invented():
    values = complete_inputs()
    values["future_undefined_field"] = None

    result = validate_required_inputs(values)

    assert result.is_valid is True
    assert result.missing_fields == ()
    assert result.not_found_fields == ()