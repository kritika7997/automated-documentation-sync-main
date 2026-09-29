from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeVar


Value = TypeVar("Value")


def normalized_text(value: str) -> str:
    return " ".join(value.split())


def compare_values(old_value: Value, new_value: Value) -> str:
    """Classify value changes without assigning policy meaning."""
    if old_value == new_value:
        return "unchanged"
    if isinstance(old_value, str) and isinstance(new_value, str):
        if normalized_text(old_value) == normalized_text(new_value):
            return "formatting_only"
    return "modified"


def keyed_changes(
    old_values: Mapping[str, Value],
    new_values: Mapping[str, Value],
) -> tuple[tuple[str, str, Value | None, Value | None], ...]:
    changes: list[tuple[str, str, Value | None, Value | None]] = []
    for key in sorted(old_values.keys() | new_values.keys()):
        if key not in old_values:
            changes.append((key, "added", None, new_values[key]))
        elif key not in new_values:
            changes.append((key, "removed", old_values[key], None))
        else:
            change_type = compare_values(old_values[key], new_values[key])
            if change_type != "unchanged":
                changes.append((key, change_type, old_values[key], new_values[key]))
    return tuple(changes)


def sequence_changes(old_values: Sequence[Value], new_values: Sequence[Value]) -> tuple[tuple[str, Value | None, Value | None], ...]:
    old_set = set(old_values)
    new_set = set(new_values)
    return tuple(
        [("removed", value, None) for value in old_values if value not in new_set]
        + [("added", None, value) for value in new_values if value not in old_set]
    )


__all__ = ["compare_values", "keyed_changes", "normalized_text", "sequence_changes"]