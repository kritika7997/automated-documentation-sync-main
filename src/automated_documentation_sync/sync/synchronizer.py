from __future__ import annotations

from typing import Any, Mapping

from automated_documentation_sync.changes.conflicts import ConflictRecord
from automated_documentation_sync.changes.detector import PolicyChange
from automated_documentation_sync.domain.clarifications import ClarificationDecision

from .change_sets import ChangeSet, build_change_set


class Synchronizer:
    """Build documentation proposals without approving or publishing them."""

    def propose(
        self,
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
        return build_change_set(
            source_version_id=source_version_id,
            clarification_version=clarification_version,
            requirements_version=requirements_version,
            configuration_snapshot=configuration_snapshot,
            changes=changes,
            clarification_impacts=clarification_impacts,
            conflicts=conflicts,
            not_found_items=not_found_items,
            out_of_scope_items=out_of_scope_items,
        )


__all__ = ["Synchronizer"]