from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser, parse_policy_document
from email.message import EmailMessage


HTML = b"""
<html>
  <head><title>Overtime Policy</title></head>
  <body>
    <h1>Overtime Compensation Policy</h1>
    <p>Effective date is 1 August 2026.</p>
    <ul>
      <li>Regular employees</li>
      <li>Subcontractors</li>
    </ul>
    <table>
      <tr><th>Version</th><th>Effective Date</th></tr>
      <tr><td>V2</td><td>01 Aug 2026</td></tr>
    </table>
    <p>Contact AskCompensation@epam.com or <a href="https://example.com/rules">review policy</a>.</p>
    <img src="attachment.png" alt="attachment" />
  </body>
</html>
"""


def make_document() -> RepositoryDocument:
    return RepositoryDocument(
        content=HTML,
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha="abc123",
        media_type="text/html",
    )


def test_policy_parser_extracts_structure_and_source_locations():
    parsed = PolicyParser().parse(make_document())

    assert parsed.raw_content == HTML
    assert parsed.normalized_text
    assert any(section.heading == "Overtime Compensation Policy" for section in parsed.sections)
    assert "Effective date is 1 August 2026." in parsed.sections[0].body
    assert len(parsed.paragraphs) >= 2
    assert any(statement.text == "Effective date is 1 August 2026." for statement in parsed.paragraphs)
    assert len(parsed.lists) >= 2
    assert any(row.cells and row.cells[0] == "Version" for row in parsed.tables[0].rows)
    assert "https://example.com/rules" in parsed.links
    assert "AskCompensation@epam.com" in parsed.email_addresses
    assert "1 August 2026" in parsed.effective_dates
    assert any(item.source_location.section == "Overtime Compensation Policy" for item in parsed.paragraphs)
    assert parsed.source_location.document_version_id == "abc123"
    assert parsed.paragraphs[0].source_location.document_version_id == "abc123"


def test_parse_policy_document_function_wraps_parser():
    parsed = parse_policy_document(make_document())

    assert parsed.raw_content == HTML
    assert parsed.sections

def test_policy_parser_preserves_mhtml_attachments_and_unresolved_references():
    message = EmailMessage()
    message.set_type("multipart/related")

    html = EmailMessage()
    html.set_content(
      '<html><body><h1>Policy</h1><img src="cid:image-1"><img src="missing.png"></body></html>',
      subtype="html",
      charset="utf-8",
    )
    message.attach(html)

    image = EmailMessage()
    image.set_content(b"image-bytes", maintype="image", subtype="png")
    image["Content-ID"] = "<image-1>"
    image["Content-Location"] = "image.png"
    message.attach(image)

    document = RepositoryDocument(
      content=message.as_bytes(),
      repository="org/policy-repository",
      path="policies/overtime-policy.doc",
      ref="main",
      commit_sha="mhtml123",
      media_type="multipart/related",
    )

    parsed = PolicyParser().parse(document)

    assert parsed.raw_content == document.content
    assert len(parsed.attachments) == 1
    assert parsed.attachments[0].content == b"image-bytes"
    assert parsed.unresolved_references == ("missing.png",)
