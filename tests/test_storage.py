from datetime import datetime, timezone

import pytest

from automated_documentation_sync.storage.models import PolicyDocumentRecord
from automated_documentation_sync.storage.repositories import DuplicateRecordError, InMemoryRepository


def test_repository_preserves_immutable_source_record():
    repository = InMemoryRepository[PolicyDocumentRecord]()
    record = PolicyDocumentRecord("doc-1", "hash-1", datetime.now(timezone.utc), "text/html", b"source")
    repository.add(record.document_id, record)
    assert repository.get("doc-1") == record


def test_repository_rejects_duplicate_immutable_record():
    repository = InMemoryRepository[str]()
    repository.add("doc-1", "source")
    with pytest.raises(DuplicateRecordError):
        repository.add("doc-1", "replacement")
