from automated_documentation_sync.sync.change_sets import ChangeSet


def render_change_set(change_set: ChangeSet) -> str:
    lines = [
        "# Documentation Change Proposal",
        "",
        f"Change set: `{change_set.change_set_id}`",
        f"Source version: `{change_set.source_version_id}`",
        f"Clarification version: `{change_set.clarification_version}`",
        f"Requirements version: `{change_set.requirements_version}`",
        "",
        "## Changes",
    ]
    if not change_set.changes:
        lines.append("No source changes.")
    for index, change in enumerate(change_set.changes, start=1):
        lines.extend(
            [
                f"### Change {index}: {change.category} ({change.change_type.value})",
                f"Classification: {change.classification.value if change.classification else 'Not Found'}",
                f"Old value: {change.old_value!r}",
                f"New value: {change.new_value!r}",
                f"Affected requirements: {', '.join(change.affected_requirement_ids) or 'None'}",
                "Source locations:",
            ]
        )
        lines.extend(f"- `{location.document_version_id}:{location.section}:{location.locator}`" for location in change.source_locations)

    lines.extend(["", "## Clarification References"])
    if not change_set.clarification_impacts:
        lines.append("None.")
    for decision in change_set.clarification_impacts:
        lines.append(
            f"- `{decision.decision_id}` ({decision.version}) -> {', '.join(decision.applicable_requirements)}"
        )

    lines.extend(["", "## Conflicts"])
    if not change_set.conflicts:
        lines.append("None.")
    for conflict in change_set.conflicts:
        lines.append(f"- `{conflict.conflict_id}` ({conflict.kind.value}): {'; '.join(conflict.values)}")

    lines.extend(["", "## Not Found"])
    lines.extend(f"- {item}" for item in change_set.not_found_items) or lines.append("None.")
    lines.extend(["", "## Out of Scope"])
    lines.extend(f"- {item}" for item in change_set.out_of_scope_items) or lines.append("None.")
    lines.extend(["", "_Proposal only. Human approval is required before finalization._", ""])
    return "\n".join(lines)


__all__ = ["render_change_set"]