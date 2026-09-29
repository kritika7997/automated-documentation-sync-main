from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser


def parse(html: str, version: str = "policy-unit-v1"):
    document = RepositoryDocument(
        content=html.encode(),
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha=version,
        media_type="text/html",
    )
    return PolicyParser().parse(document)


def test_policy_parser_happy_path_preserves_structure_and_locations():
    parsed = parse(
        "<html><body><h1>Policy</h1><p>Wage Salary rule.</p>"
        "<ul><li>Working day</li></ul><table><tr><td>V2</td></tr></table>"
        "<a href='https://example.test/policy'>policy</a></body></html>"
    )

    assert parsed.sections[0].heading == "Policy"
    assert parsed.paragraphs[0].text == "Wage Salary rule."
    assert parsed.lists[0].text == "Working day"
    assert parsed.tables[0].rows[0].cells == ("V2",)
    assert parsed.links == ("https://example.test/policy",)
    assert parsed.paragraphs[0].source_location.document_version_id == "policy-unit-v1"


def test_faq_only_content_is_classified_separately_from_policy_statements():
    parsed = parse(
        "<html><body><h1>FAQ</h1><p>What is the threshold? 6 hours.</p>"
        "<p>Who is the contact? faq@example.com.</p></body></html>"
    )

    assert parsed.faq_entries[0].question == "What is the threshold?"
    assert parsed.faq_entries[0].answer == "6 hours."
    assert parsed.faq_entries[0].source_location.section == "FAQ"
    assert parsed.faq_entries[0].classification.value == "Source FAQ"
    assert parsed.email_addresses == ("faq@example.com",)


def test_malformed_html_is_retained_while_parser_returns_available_text():
    raw = "<html><body><h1>Policy</h2><p>Raw policy</p>"

    parsed = parse(raw)

    assert parsed.raw_content == raw.encode()
    assert "Raw policy" in parsed.normalized_text
    assert parsed.sections