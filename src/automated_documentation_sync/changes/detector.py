from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.domain.policy_model import (
    CanonicalPolicyModel,
    CanonicalStatement,
)

from .comparators import compare_values, keyed_changes, sequence_changes


class ChangeType(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    FORMATTING_ONLY = "formatting_only"


@dataclass(frozen=True)
class PolicyChange:
    change_type: ChangeType
    category: str
    old_value: object | None
    new_value: object | None
    source_locations: tuple[SourceLocation, ...]
    classification: Classification | None
    affected_requirement_ids: tuple[str, ...] = ()


def _statements(policy: CanonicalPolicyModel) -> dict[str, CanonicalStatement]:
    section_positions: dict[str, int] = {}
    values: dict[str, CanonicalStatement] = {}
    for statement in policy.statements:
        section = statement.source_location.section
        position = section_positions.get(section, 0)
        section_positions[section] = position + 1
        values[f"{section}:{position}"] = statement
    return values


def _change_type(value: str) -> ChangeType:
    return ChangeType(value)


def _statement_changes(
    previous: CanonicalPolicyModel,
    current: CanonicalPolicyModel,
    requirement_ids: tuple[str, ...],
) -> list[PolicyChange]:
    changes: list[PolicyChange] = []
    for key, kind, old, new in keyed_changes(_statements(previous), _statements(current)):
        old_statement = old if isinstance(old, CanonicalStatement) else None
        new_statement = new if isinstance(new, CanonicalStatement) else None
        if old_statement is not None and new_statement is not None:
            kind = compare_values(old_statement.normalized_text, new_statement.normalized_text)
            if kind == "unchanged":
                if old_statement.raw_text == new_statement.raw_text:
                    continue
                kind = "formatting_only"
        locations = tuple(
            location
            for location in (
                old_statement.source_location if old_statement else None,
                new_statement.source_location if new_statement else None,
            )
            if location is not None
        )
        changes.append(
            PolicyChange(
                change_type=_change_type(kind),
                category="statement",
                old_value=old_statement.raw_text if old_statement else None,
                new_value=new_statement.raw_text if new_statement else None,
                source_locations=locations,
                classification=(new_statement or old_statement).classification if (new_statement or old_statement) else None,
                affected_requirement_ids=requirement_ids,
            )
        )
    return changes


def _faq_changes(
    previous: CanonicalPolicyModel,
    current: CanonicalPolicyModel,
    requirement_ids: tuple[str, ...],
) -> list[PolicyChange]:
    old_values = {
        f"{entry.source_location.section}:{position}": entry
        for position, entry in enumerate(previous.faq_entries)
    }
    new_values = {
        f"{entry.source_location.section}:{position}": entry
        for position, entry in enumerate(current.faq_entries)
    }
    changes: list[PolicyChange] = []
    for key, kind, old, new in keyed_changes(old_values, new_values):
        old_entry = old if old is not None else None
        new_entry = new if new is not None else None
        locations = tuple(
            entry.source_location
            for entry in (old_entry, new_entry)
            if entry is not None
        )
        old_value = f"{old_entry.question} {old_entry.answer or ''}".strip() if old_entry else None
        new_value = f"{new_entry.question} {new_entry.answer or ''}".strip() if new_entry else None
        changes.append(
            PolicyChange(
                change_type=_change_type(kind),
                category="faq",
                old_value=old_value,
                new_value=new_value,
                source_locations=locations,
                classification=(new_entry or old_entry).classification if (new_entry or old_entry) else None,
                affected_requirement_ids=requirement_ids,
            )
        )
    return changes


def _sequence_changes(
    category: str,
    old_values: tuple[str, ...],
    new_values: tuple[str, ...],
    location: SourceLocation,
    requirement_ids: tuple[str, ...],
) -> list[PolicyChange]:
    return [
        PolicyChange(
            change_type=ChangeType(kind),
            category=category,
            old_value=old_value,
            new_value=new_value,
            source_locations=(location,),
            classification=Classification.SOURCE_POLICY,
            affected_requirement_ids=requirement_ids,
        )
        for kind, old_value, new_value in sequence_changes(old_values, new_values)
    ]


def compare_policy_versions(
    previous: CanonicalPolicyModel,
    current: CanonicalPolicyModel,
    *,
    affected_requirement_ids: tuple[str, ...] = (),
) -> tuple[PolicyChange, ...]:
    """Compare canonical versions without resolving conflicts or policy authority."""
    if previous.policy_version_id == current.policy_version_id:
        raise ValueError("Policy versions must have distinct identifiers")

    changes = _statement_changes(previous, current, affected_requirement_ids)
    changes.extend(_faq_changes(previous, current, affected_requirement_ids))
    location = current.statements[0].source_location if current.statements else SourceLocation(
        document_version_id=current.policy_version_id,
        section="policy",
        locator="document",
    )
    for category, old_values, new_values in (
        ("formula", previous.formulas, current.formulas),
        ("threshold", previous.thresholds, current.thresholds),
        ("contact", previous.contacts, current.contacts),
        ("date", previous.dates, current.dates),
    ):
        changes.extend(_sequence_changes(category, old_values, new_values, location, affected_requirement_ids))

    old_tables = tuple(tuple(row.cells for row in table.rows) for table in previous.tables)
    new_tables = tuple(tuple(row.cells for row in table.rows) for table in current.tables)
    if old_tables != new_tables:
        changes.append(
            PolicyChange(
                change_type=ChangeType.MODIFIED,
                category="table",
                old_value=old_tables,
                new_value=new_tables,
                source_locations=(location,),
                classification=Classification.SOURCE_POLICY,
                affected_requirement_ids=affected_requirement_ids,
            )
        )
    return tuple(changes)


__all__ = ["ChangeType", "PolicyChange", "compare_policy_versions"]