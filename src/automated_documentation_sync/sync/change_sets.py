from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from automated_documentation_sync.changes.conflicts import ConflictRecord
from automated_documentation_sync.changes.detector import PolicyChange
from automated_documentation_sync.domain.clarifications import ClarificationDecision


class ChangeSetError(ValueError):
    """Raised when a synchronization change set lacks required provenance."""


@dataclass(frozen=True)
class ChangeSet:
    change_set_id: str
    source_version_id: str
    clarification_version: str
    requirements_version: str
    configuration_snapshot: tuple[tuple[str, Any], ...]
    changes: tuple[PolicyChange, ...]
    clarification_impacts: tuple[ClarificationDecision, ...]
    conflicts: tuple[ConflictRecord, ...]
    not_found_items: tuple[str, ...]
    out_of_scope_items: tuple[str, ...]
    is_proposal: bool = True

    def clarification_precedence(self, requirement_id: str) -> tuple[ClarificationDecision, ...]:
        return tuple(
            decision
            for decision in self.clarification_impacts
            if requirement_id in decision.applicable_requirements
        )


def _configuration_snapshot(values: Mapping[str, Any]) -> tuple[tuple[str, Any], ...]:
    snapshot = tuple(sorted(values.items(), key=lambda item: item[0]))
    try:
        json.dumps(snapshot, sort_keys=True, default=None)
    except TypeError as exc:
        raise ChangeSetError("Configuration snapshot must contain serializable values") from exc
    return snapshot


def _identity_payload(
    source_version_id: str,
    clarification_version: str,
    requirements_version: str,
    configuration_snapshot: tuple[tuple[str, Any], ...],
    changes: tuple[PolicyChange, ...],
    clarification_impacts: tuple[ClarificationDecision, ...],
    conflicts: tuple[ConflictRecord, ...],
    not_found_items: tuple[str, ...],
    out_of_scope_items: tuple[str, ...],
) -> bytes:
    payload = {
        "source_version_id": source_version_id,
        "clarification_version": clarification_version,
        "requirements_version": requirements_version,
        "configuration_snapshot": configuration_snapshot,
        "changes": changes,
        "clarification_impacts": clarification_impacts,
        "conflicts": conflicts,
        "not_found_items": not_found_items,
        "out_of_scope_items": out_of_scope_items,
    }
    try:
        return json.dumps(payload, default=lambda value: value.__dict__, sort_keys=True, separators=(",", ":")).encode()
    except TypeError as exc:
        raise ChangeSetError("Change set inputs must be serializable") from exc


def build_change_set(
    *,
    source_version_id: str,
    clarification_version: str,
    requirements_version: str,
    configuration_snapshot: Mapping[str, Any],
    changes: tuple[PolicyChange, ...] = (),
    clarification_impacts: tuple[ClarificationDecision, ...] = (),
    conflicts: tuple[ConflictRecord, ...] = (),
    not_found_items: tuple[str, ...] = (),
    out_of_scope_items: tuple[str, ...] = (),
) -> ChangeSet:
    if not source_version_id or not clarification_version or not requirements_version:
        raise ChangeSetError("Source, clarification, and requirements versions are required")
    snapshot = _configuration_snapshot(configuration_snapshot)
    payload = _identity_payload(
        source_version_id,
        clarification_version,
        requirements_version,
        snapshot,
        changes,
        clarification_impacts,
        conflicts,
        not_found_items,
        out_of_scope_items,
    )
    return ChangeSet(
        change_set_id=hashlib.sha256(payload).hexdigest(),
        source_version_id=source_version_id,
        clarification_version=clarification_version,
        requirements_version=requirements_version,
        configuration_snapshot=snapshot,
        changes=changes,
        clarification_impacts=clarification_impacts,
        conflicts=conflicts,
        not_found_items=not_found_items,
        out_of_scope_items=out_of_scope_items,
    )


__all__ = ["ChangeSet", "ChangeSetError", "build_change_set"]