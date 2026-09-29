import pytest

from automated_documentation_sync.config.schema import ConfigurationError, require_project_configuration


def test_configuration_accepts_only_eight_or_nine_working_hours():
    configuration = require_project_configuration({
        "week_start_day": "Monday",
        "time_zone": "Asia/Kolkata",
        "working_hours": 8,
        "calendar_reference": "project-calendar",
    })
    assert configuration.working_hours == 8


@pytest.mark.parametrize("working_hours", [7, 10, 0])
def test_configuration_rejects_invalid_working_hours(working_hours):
    with pytest.raises(ConfigurationError):
        require_project_configuration({
            "week_start_day": "Monday",
            "time_zone": "Asia/Kolkata",
            "working_hours": working_hours,
            "calendar_reference": "project-calendar",
        })


def test_configuration_rejects_missing_values_without_defaults():
    with pytest.raises(ConfigurationError, match="Not Found"):
        require_project_configuration({"working_hours": 9})


@pytest.mark.parametrize("week_start_day", ["Funday", ""])
def test_configuration_rejects_invalid_week_start_day(week_start_day):
    with pytest.raises(ConfigurationError):
        require_project_configuration({
            "week_start_day": week_start_day,
            "time_zone": "Asia/Kolkata",
            "working_hours": 8,
            "calendar_reference": "project-calendar",
        })


def test_configuration_rejects_invalid_time_zone():
    with pytest.raises(ConfigurationError):
        require_project_configuration({
            "week_start_day": "Monday",
            "time_zone": "InvalidTimezone",
            "working_hours": 8,
            "calendar_reference": "project-calendar",
        })
