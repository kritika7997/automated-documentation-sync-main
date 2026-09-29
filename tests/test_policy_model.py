import hashlib

import pytest

from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.policy_model import build_canonical_policy
from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser
from automated_documentation_sync.storage.policy_repository import PolicyRepository
from automated_documentation_sync.storage.repositories import DuplicateRecordError


def make_document() -> RepositoryDocument:
    return RepositoryDocument(
        content=b"""
        <html><body>
          <h1>Overtime Policy</h1>
          <p>Hourly wage = Wage Salary / 365 / 8 hours.</p>
          <p>Non-working-day threshold is 6 hours.</p>
          <h2>FAQ</h2>
          <p>Where should details go? Contact faq@example.com.</p>
          <table><tr><th>Version</th><th>Date</th></tr><tr><td>V2</td><td>1 August 2026</td></tr></table>
        </body></html>
        """,
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha="policy-v2",
        media_type="text/html",
    )


def test_canonical_policy_preserves_raw_normalized_and_structured_records():
    source = make_document()
    canonical = build_canonical_policy(PolicyParser().parse(source))

    assert canonical.policy_version_id == "policy-v2"
    assert canonical.raw_content == source.content
    assert canonical.raw_content_hash == hashlib.sha256(source.content).hexdigest()
    assert canonical.normalized_text
    assert canonical.statements[0].classification is Classification.SOURCE_POLICY
    assert canonical.statements[0].raw_text == canonical.statements[0].normalized_text
    assert canonical.statements[0].source_location.document_version_id == "policy-v2"
    assert canonical.formulas
    assert canonical.thresholds
    assert canonical.contacts == ("faq@example.com",)
    assert canonical.dates == ("1 August 2026",)
    assert canonical.faq_entries[0].classification is Classification.SOURCE_FAQ
    assert canonical.tables
    assert canonical.conflict_flags == ()


def test_policy_repository_round_trips_immutable_canonical_record():
    canonical = build_canonical_policy(PolicyParser().parse(make_document()))
    repository = PolicyRepository()

    repository.add(canonical)

    assert repository.get("policy-v2") == canonical
    with pytest.raises(DuplicateRecordError):
        repository.add(canonical)