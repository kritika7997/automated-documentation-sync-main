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
from automated_documentation_sync.versioning.version_registry import (
    PARSER_VERSION,
    create_policy_version,
)


def make_policy(content: bytes, commit_sha: str):
    document = RepositoryDocument(
        content=content,
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha=commit_sha,
        media_type="text/html",
    )
    return build_canonical_policy(PolicyParser().parse(document))


def test_policy_version_preserves_hash_parser_timestamp_and_effective_date():
    policy = make_policy(
        b"<html><body><h1>Policy</h1><p>Effective 1 August 2026.</p></body></html>",
        "v1",
    )
    received_at = datetime(2026, 9, 8, tzinfo=timezone.utc)

    version = create_policy_version(policy, received_at=received_at)

    assert version.version_id == "v1"
    assert version.source_hash == policy.raw_content_hash
    assert version.parser_version == PARSER_VERSION
    assert version.received_at == received_at
    assert version.effective_date == "1 August 2026"
    assert version.predecessor_id is None


def test_registry_rejects_duplicate_hash_and_preserves_predecessor_linkage():
    repository = VersionRepository()
    first = create_policy_version(
        make_policy(b"<html><body><h1>Policy</h1><p>Version one.</p></body></html>", "v1"),
        received_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
    )
    second = create_policy_version(
        make_policy(b"<html><body><h1>Policy</h1><p>Version two.</p></body></html>", "v2"),
        received_at=datetime(2026, 9, 9, tzinfo=timezone.utc),
        predecessor_id="v1",
    )

    repository.add(first)
    repository.add(second)

    assert repository.get("v1") == first
    assert repository.get_successor("v1") == second
    assert second.supersedes_id == "v1"

    duplicate = create_policy_version(
        make_policy(b"<html><body><h1>Policy</h1><p>Version one.</p></body></html>", "v3"),
        received_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
    )
    with pytest.raises(DuplicateVersionHashError):
        repository.add(duplicate)


def test_registry_rejects_unknown_or_reused_predecessor():
    repository = VersionRepository()
    version = create_policy_version(
        make_policy(b"<html><body><h1>Policy</h1><p>Version one.</p></body></html>", "v1"),
        received_at=datetime(2026, 9, 8, tzinfo=timezone.utc),
    )

    with pytest.raises(InvalidVersionLineageError):
        repository.add(
            create_policy_version(
                make_policy(b"<html><body><h1>Policy</h1><p>Version two.</p></body></html>", "v2"),
                received_at=datetime(2026, 9, 9, tzinfo=timezone.utc),
                predecessor_id="missing",
            )
        )

    repository.add(version)
    successor = create_policy_version(
        make_policy(b"<html><body><h1>Policy</h1><p>Version two.</p></body></html>", "v2"),
        received_at=datetime(2026, 9, 9, tzinfo=timezone.utc),
        predecessor_id="v1",
    )
    repository.add(successor)
    with pytest.raises(InvalidVersionLineageError):
        repository.add(
            create_policy_version(
                make_policy(b"<html><body><h1>Policy</h1><p>Version three.</p></body></html>", "v3"),
                received_at=datetime(2026, 9, 10, tzinfo=timezone.utc),
                predecessor_id="v1",
            )
        )