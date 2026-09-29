from datetime import datetime

import pytest

from automated_documentation_sync.ingestion import (
    GitHubPolicySourceAdapter,
    InvalidSourceDocument,
    RepositoryDocument,
    SourceRepositoryConfiguration,
    SourceDocumentNotFound,
    SourceRepositoryUnavailable,
)


class MockRepositoryClient:
    def __init__(self, document=None, error=None):
        self.document = document
        self.error = error
        self.calls = []

    def get_document(self, repository, path, ref):
        self.calls.append((repository, path, ref))
        if self.error:
            raise self.error
        return self.document


def make_document():
    return RepositoryDocument(
        content=b"approved policy source",
        repository="org/policy-repository",
        path="policies/overtime.doc",
        ref="main",
        commit_sha="abc123",
        media_type="application/msword",
    )


def make_configuration():
    return SourceRepositoryConfiguration(
        owner="org",
        name="policy-repository",
        document_path="policies/overtime.doc",
        ref="main",
    )


def test_retrieves_raw_document_and_provenance_metadata():
    client = MockRepositoryClient(make_document())
    adapter = GitHubPolicySourceAdapter(client, make_configuration())

    source = adapter.retrieve()

    assert source.content == b"approved policy source"
    assert len(source.content_hash) == 64
    assert source.repository == "org/policy-repository"
    assert source.path == "policies/overtime.doc"
    assert source.ref == "main"
    assert source.commit_sha == "abc123"
    assert isinstance(source.fetched_at, datetime)
    assert client.calls == [("org/policy-repository", "policies/overtime.doc", "main")]


def test_missing_document_fails_safely():
    client = MockRepositoryClient()
    configuration = SourceRepositoryConfiguration("org", "policy-repository", "missing.doc", "main")
    adapter = GitHubPolicySourceAdapter(client, configuration)

    with pytest.raises(SourceDocumentNotFound):
        adapter.retrieve()


def test_repository_failure_is_wrapped_without_exposing_credentials():
    client = MockRepositoryClient(error=RuntimeError("transport failed"))
    adapter = GitHubPolicySourceAdapter(client, make_configuration())

    with pytest.raises(SourceRepositoryUnavailable) as error:
        adapter.retrieve()

    assert "transport failed" not in str(error.value)


def test_configuration_requires_repository_path_and_ref():
    with pytest.raises(ValueError):
        SourceRepositoryConfiguration("", "policy-repository", "policy.doc", "main")


def test_invalid_repository_response_fails_safely():
    client = MockRepositoryClient(document={"content": "not a repository document"})
    adapter = GitHubPolicySourceAdapter(client, make_configuration())

    with pytest.raises(InvalidSourceDocument):
        adapter.retrieve()
