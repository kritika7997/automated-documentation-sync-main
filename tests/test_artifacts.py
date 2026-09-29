import hashlib

import pytest

from automated_documentation_sync.generation.artifacts import create_artifact_snapshot
from automated_documentation_sync.generation.renderer import DocumentationProposal
from automated_documentation_sync.storage.artifact_repository import ArtifactRepository
from automated_documentation_sync.storage.repositories import DuplicateRecordError


def proposal(content: str = "# Proposal") -> DocumentationProposal:
    return DocumentationProposal(
        change_set_id="change-set-1",
        source_version_id="source-v2",
        clarification_version="clarifications-v1",
        requirements_version="requirements-v1",
        content=content,
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
    )


def test_artifact_hash_is_deterministic_and_linked_to_change_set_versions():
    first = create_artifact_snapshot(proposal())
    second = create_artifact_snapshot(proposal())

    assert first == second
    assert first.content == b"# Proposal"
    assert first.content_hash == hashlib.sha256(first.content).hexdigest()
    assert first.change_set_id == "change-set-1"
    assert first.source_version_id == "source-v2"
    assert first.clarification_version == "clarifications-v1"


def test_changed_content_produces_a_different_artifact_hash():
    first = create_artifact_snapshot(proposal("# Proposal"))
    changed = create_artifact_snapshot(proposal("# Changed proposal"))

    assert first.content_hash != changed.content_hash
    assert first.artifact_id != changed.artifact_id


def test_artifact_repository_preserves_immutable_snapshot():
    repository = ArtifactRepository()
    artifact = create_artifact_snapshot(proposal())

    repository.add(artifact)

    assert repository.get(artifact.artifact_id) == artifact
    with pytest.raises(DuplicateRecordError):
        repository.add(artifact)