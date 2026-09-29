from datetime import datetime, timezone

import pytest

from automated_documentation_sync.domain.policy_model import build_canonical_policy
from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser
from automated_documentation_sync.storage.version_repository import (
    DuplicateVersionHashError,
    InvalidVersionLineageError,
    VersionRepository,
)
from automated_documentation_sync.versioning.version_registry import create_policy_version


def policy(html: str, version: str):
    document = RepositoryDocument(
        content=html.encode(),
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha=version,
        media_type="text/html",
    )
    return build_canonical_policy(PolicyParser().parse(document))


def test_version_registry_preserves_immutable_metadata_and_predecessor():
    repository = VersionRepository()
    first = create_policy_version(
        policy("<html><body><h1>Policy</h1><p>Version one.</p></body></html>", "version-1"),
        received_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )
    second = create_policy_version(
        policy("<html><body><h1>Policy</h1><p>Version two.</p></body></html>", "version-2"),
        received_at=datetime(2026, 9, 16, tzinfo=timezone.utc),
        predecessor_id="version-1",
    )

    repository.add(first)
    repository.add(second)

    assert repository.get("version-1") == first
    assert repository.get_successor("version-1") == second
    assert second.supersedes_id == "version-1"
    assert first.source_hash != second.source_hash


def test_version_registry_rejects_duplicate_hash_and_invalid_lineage():
    repository = VersionRepository()
    first_policy = policy("<html><body><h1>Policy</h1><p>Same content.</p></body></html>", "version-1")
    repository.add(
        create_policy_version(
            first_policy,
            received_at=datetime(2026, 9, 15, tzinfo=timezone.utc),
        )
    )

    with pytest.raises(DuplicateVersionHashError):
        repository.add(
            create_policy_version(
                policy(first_policy.raw_content.decode(), "version-2"),
                received_at=datetime(2026, 9, 16, tzinfo=timezone.utc),
            )
        )
    with pytest.raises(InvalidVersionLineageError):
        repository.add(
            create_policy_version(
                policy("<html><body><h1>Policy</h1><p>New content.</p></body></html>", "version-3"),
                received_at=datetime(2026, 9, 17, tzinfo=timezone.utc),
                predecessor_id="missing-version",
            )
        )