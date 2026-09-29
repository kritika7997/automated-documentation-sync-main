from __future__ import annotations

import hashlib
from dataclasses import dataclass

from automated_documentation_sync.sync.change_sets import ChangeSet

from .templates import render_change_set


@dataclass(frozen=True)
class DocumentationProposal:
    change_set_id: str
    source_version_id: str
    clarification_version: str
    requirements_version: str
    content: str
    content_hash: str
    is_proposal: bool = True


def render_proposal(change_set: ChangeSet) -> DocumentationProposal:
    """Render a deterministic review proposal without publishing or finalizing it."""
    content = render_change_set(change_set)
    return DocumentationProposal(
        change_set_id=change_set.change_set_id,
        source_version_id=change_set.source_version_id,
        clarification_version=change_set.clarification_version,
        requirements_version=change_set.requirements_version,
        content=content,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


__all__ = ["DocumentationProposal", "render_proposal"]