import html
import re

from automated_documentation_sync.sync.change_sets import ChangeSet


def _markdown_text(value: object) -> str:
    text = " ".join(str(value).split())
    text = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+\-.!|])", r"\\\1", text)


def _code_span(value: object) -> str:
    text = str(value)
    longest_backticks = max(
        (len(match.group(0)) for match in re.finditer(r"`+", text)),
        default=0,
    )
    fence = "`" * (longest_backticks + 1)
    if (
        text.startswith("`")
        or text.endswith("`")
        or (text.startswith(" ") and text.endswith(" ") and bool(text.strip()))
    ):
        text = f" {text} "
    return f"{fence}{text}{fence}"


def render_change_set(change_set: ChangeSet) -> str:
    lines = [
        "# Documentation Change Proposal",
        "",
        f"Change set: {_code_span(change_set.change_set_id)}",
        f"Source version: {_code_span(change_set.source_version_id)}",
        f"Clarification version: {_code_span(change_set.clarification_version)}",
        f"Requirements version: {_code_span(change_set.requirements_version)}",
        "",
        "## Changes",
    ]
    if not change_set.changes:
        lines.append("No source changes.")
    for index, change in enumerate(change_set.changes, start=1):
        lines.extend(
            [
                f"### Change {index}: {_markdown_text(change.category)} ({_markdown_text(change.change_type.value)})",
                f"Classification: {_markdown_text(change.classification.value if change.classification else 'Not Found')}",
                f"Old value: {_code_span(repr(change.old_value))}",
                f"New value: {_code_span(repr(change.new_value))}",
                f"Affected requirements: {', '.join(_code_span(item) for item in change.affected_requirement_ids) or 'None'}",
                "Source locations:",
            ]
        )
        lines.extend(
            f"- {_code_span(f'{location.document_version_id}:{location.section}:{location.locator}')}"
            for location in change.source_locations
        )

    lines.extend(["", "## Clarification References"])
    if not change_set.clarification_impacts:
        lines.append("None.")
    for decision in change_set.clarification_impacts:
        lines.append(
            f"- {_code_span(decision.decision_id)} ({_code_span(decision.version)}) -> "
            f"{', '.join(_code_span(item) for item in decision.applicable_requirements)}"
        )

    lines.extend(["", "## Conflicts"])
    if not change_set.conflicts:
        lines.append("None.")
    for conflict in change_set.conflicts:
        lines.append(
            f"- {_code_span(conflict.conflict_id)} ({_code_span(conflict.kind.value)}): "
            f"{'; '.join(_code_span(item) for item in conflict.values)}"
        )

    lines.extend(["", "## Not Found"])
    lines.extend(f"- {_code_span(item)}" for item in change_set.not_found_items) or lines.append("None.")
    lines.extend(["", "## Out of Scope"])
    lines.extend(f"- {_code_span(item)}" for item in change_set.out_of_scope_items) or lines.append("None.")
    lines.extend(["", "_Proposal only. Human approval is required before finalization._", ""])
    return "\n".join(lines)


__all__ = ["render_change_set"]