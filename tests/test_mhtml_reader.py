from email.message import EmailMessage

from automated_documentation_sync.ingestion import (
    RepositoryDocument,
    extract_source_package,
    read_source_document,
)


def make_mhtml() -> bytes:
    message = EmailMessage()
    message.set_type("multipart/related")

    html = EmailMessage()
    html.set_content(
        '<html><body><img src="cid:image-1"><a href="missing.css">link</a></body></html>',
        subtype="html",
        charset="utf-8",
    )
    message.attach(html)

    image = EmailMessage()
    image.set_content(b"image-bytes", maintype="image", subtype="png")
    image["Content-ID"] = "<image-1>"
    image["Content-Location"] = "image.png"
    message.attach(image)

    return message.as_bytes()


def make_document(content: bytes, media_type: str) -> RepositoryDocument:
    return RepositoryDocument(
        content=content,
        repository="org/policy-repository",
        path="policies/overtime.doc",
        ref="main",
        commit_sha="abc123",
        media_type=media_type,
    )


def test_mhtml_decodes_html_and_embedded_resources():
    parsed = read_source_document(make_document(make_mhtml(), "multipart/related"))

    assert b"<html>" in parsed.html_content
    assert len(parsed.resources) == 1
    assert parsed.resources[0].content == b"image-bytes"
    assert parsed.resources[0].content_id == "<image-1>"
    assert parsed.resources[0].content_location == "image.png"
    assert parsed.unresolved_references == ("missing.css",)


def test_non_multipart_html_is_preserved_without_attachments():
    content = b"<html><body>policy</body></html>"
    parsed = read_source_document(make_document(content, "text/html"))

    assert parsed.raw_content == content
    assert parsed.html_content == content
    assert parsed.resources == ()
    assert parsed.unresolved_references == ()


def test_source_package_retains_original_document_and_attachments():
    document = make_document(make_mhtml(), "multipart/related")
    package = extract_source_package(document)

    assert package.document is document
    assert package.attachments == package.parsed.resources
