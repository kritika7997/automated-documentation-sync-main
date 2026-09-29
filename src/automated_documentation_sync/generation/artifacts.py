from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .renderer import DocumentationProposal


@dataclass(frozen=True)
class ArtifactSnapshot:
    artifact_id: str
    change_set_id: str
    source_version_id: str
    clarification_version: str
    content: bytes
    content_hash: str


def create_artifact_snapshot(proposal: DocumentationProposal) -> ArtifactSnapshot:
    content = proposal.content.encode("utf-8")
    content_hash = hashlib.sha256(content).hexdigest()
    artifact_id = hashlib.sha256(f"{proposal.change_set_id}:{content_hash}".encode("utf-8")).hexdigest()
    return ArtifactSnapshot(
        artifact_id=artifact_id,
        change_set_id=proposal.change_set_id,
        source_version_id=proposal.source_version_id,
        clarification_version=proposal.clarification_version,
        content=content,
        content_hash=content_hash,
    )


__all__ = ["ArtifactSnapshot", "create_artifact_snapshot"]