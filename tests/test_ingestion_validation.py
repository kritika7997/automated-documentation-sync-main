import pytest

from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.ingestion.validation import (
    DocumentValidationResult,
    EmptyOrInvalidDocumentError,
    validate_document_for_sync,
)
from automated_documentation_sync.workflow.checkpoints import (
    CheckpointStore,
    SYNC_FAILED,
    SynchronizationCheckpoint,
)


def make_document(content: bytes, media_type: str = "text/html") -> RepositoryDocument:
    return RepositoryDocument(
        content=content,
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha="abc123",
        media_type=media_type,
    )


def test_valid_document_is_allowed_to_continue():
    result = validate_document_for_sync(make_document(b"<html><body>policy content</body></html>"), run_id="run-valid")

    assert isinstance(result, DocumentValidationResult)
    assert result.is_valid is True
    assert result.requires_human_review is False
    assert result.documentation_update_allowed is True
    assert result.checkpoint.state == "SYNC_INGESTED"


@pytest.mark.parametrize("body", [b"", b"   \n\t  ", b"<html><body> </body></html>", b"<div></div>"])
def test_empty_or_contentless_document_is_rejected_with_sync_failed_checkpoint(body):
    result = validate_document_for_sync(make_document(body), run_id="run-empty")

    assert result.is_valid is False
    assert result.requires_human_review is True
    assert result.documentation_update_allowed is False
    assert result.checkpoint.state == SYNC_FAILED
    assert result.checkpoint.raw_content == body
    assert result.reason.lower().startswith("empty") or "contentless" in result.reason.lower()

    store = CheckpointStore()
    store.record(result.checkpoint)
    assert store.get("run-empty") == result.checkpoint


def test_malformed_package_is_rejected_without_document_update():
    document = make_document(b"not-a-valid-message", media_type="multipart/related")

    with pytest.raises(EmptyOrInvalidDocumentError):
        validate_document_for_sync(document, run_id="run-invalid", raise_on_invalid=True)

    result = validate_document_for_sync(document, run_id="run-invalid-2")
    assert result.is_valid is False
    assert result.documentation_update_allowed is False
    assert result.checkpoint.state == SYNC_FAILED


def test_checkpoint_records_original_bytes_for_audit():
    document = make_document(b"<html><body>policy</body></html>")
    result = validate_document_for_sync(document, run_id="audit-run")

    assert result.checkpoint.raw_content == document.content
    assert isinstance(result.checkpoint, SynchronizationCheckpoint)
