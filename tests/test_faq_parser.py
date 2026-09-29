from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser


def make_document(faq_body: str) -> RepositoryDocument:
    content = f"""
    <html><body>
      <h1>Source Policy</h1><p>Policy wording.</p>
      <h2>FAQ</h2>{faq_body}
    </body></html>
    """.encode()
    return RepositoryDocument(
        content=content,
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha="faq123",
        media_type="text/html",
    )


def test_faq_entries_are_separate_and_classified_with_source_location():
    parsed = PolicyParser().parse(make_document("<p>How is overtime handled? It is reviewed.</p>"))

    entry = parsed.faq_entries[0]
    assert entry.question == "How is overtime handled?"
    assert entry.answer == "It is reviewed."
    assert entry.classification is Classification.SOURCE_FAQ
    assert entry.source_location.section == "FAQ"
    assert entry.source_location.document_version_id == "faq123"
    assert parsed.paragraphs[0].source_location.section == "Source Policy"


def test_incomplete_faq_entry_is_retained_and_marked_incomplete():
    parsed = PolicyParser().parse(make_document("<p>Who approves overtime?</p>"))

    entry = parsed.faq_entries[0]
    assert entry.question == "Who approves overtime?"
    assert entry.answer is None
    assert entry.incomplete is True


def test_faq_preserves_six_hour_threshold_and_contact_conflicts():
    parsed = PolicyParser().parse(
        make_document(
            "<p>What is the threshold? Approved non-working-day overtime from 6 hours is eligible.</p>"
            "<p>Where should subcontractor details go? Contact faq-team@example.com.</p>"
        )
    )

    assert "6 hours" in parsed.faq_entries[0].answer
    assert parsed.faq_entries[1].email_addresses == ("faq-team@example.com",)
    assert parsed.email_addresses == ("faq-team@example.com",)