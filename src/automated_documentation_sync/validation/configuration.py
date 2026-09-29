from typing import Any

from automated_documentation_sync.config.schema import (
    ConfigurationError,
    ProjectConfiguration,
    require_project_configuration,
)


def validate_project_configuration(values: dict[str, Any]) -> ProjectConfiguration:
    """Validate project configuration without supplying policy defaults."""
    return require_project_configuration(values)


__all__ = ["ConfigurationError", "ProjectConfiguration", "validate_project_configuration"]