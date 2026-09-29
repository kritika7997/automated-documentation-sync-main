from email.message import EmailMessage

from automated_documentation_sync.ingestion import RepositoryDocument, read_source_document
from automated_documentation_sync.ingestion.validation import validate_document_for_sync
from automated_documentation_sync.workflow.checkpoints import SYNC_FAILED


def document(content: bytes, media_type: str = "text/html") -> RepositoryDocument:
    return RepositoryDocument(
        content=content,
        repository="org/policy-repository",
        path="policies/overtime-policy.doc",
        ref="main",
        commit_sha="unit-v1",
        media_type=media_type,
    )


def mhtml_without_image() -> bytes:
    message = EmailMessage()
    message.set_type("multipart/related")
    html = EmailMessage()
    html.set_content(
        '<html><body><img src="missing.png">policy</body></html>',
        subtype="html",
        charset="utf-8",
    )
    message.attach(html)
    return message.as_bytes()


def test_mhtml_capture_preserves_raw_package_and_decoded_body():
    raw = mhtml_without_image()

    parsed = read_source_document(document(raw, "multipart/related"))

    assert parsed.raw_content == raw
    assert b"policy" in parsed.html_content
    assert parsed.resources == ()
    assert parsed.unresolved_references == ("missing.png",)


def test_malformed_multipart_fails_closed_without_update():
    result = validate_document_for_sync(
        document(b"not-a-valid-mime-message", "multipart/related"),
        run_id="malformed-unit-run",
    )

    assert result.is_valid is False
    assert result.documentation_update_allowed is False
    assert result.checkpoint.state == SYNC_FAILED
    assert result.checkpoint.raw_content == b"not-a-valid-mime-message"


def test_empty_input_is_preserved_and_requires_review():
    result = validate_document_for_sync(document(b""), run_id="empty-unit-run")

    assert result.is_valid is False
    assert result.requires_human_review is True
    assert result.checkpoint.raw_content == b""
    assert result.checkpoint.state == SYNC_FAILED