from __future__ import annotations

import html
import re
from dataclasses import dataclass

from ..workflow.checkpoints import CheckpointStore, SynchronizationCheckpoint, SYNC_FAILED
from .contracts import RepositoryDocument
from .mhtml_reader import read_source_document


class EmptyOrInvalidDocumentError(ValueError):
    """Raised when a source document is empty or malformed and cannot proceed."""


@dataclass(frozen=True)
class DocumentValidationResult:
    document: RepositoryDocument
    is_valid: bool
    reason: str
    checkpoint: SynchronizationCheckpoint
    requires_human_review: bool
    documentation_update_allowed: bool


def _normalized_text(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace")
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return " ".join(text.split())


def _document_has_content(payload: bytes) -> bool:
    return bool(_normalized_text(payload))


def _checkpoint_for(
    *,
    run_id: str,
    document: RepositoryDocument,
    state: str,
    reason: str,
    requires_human_review: bool,
    documentation_update_allowed: bool,
) -> SynchronizationCheckpoint:
    source_id = f"{document.repository}:{document.path}@{document.ref}:{document.commit_sha}"
    return SynchronizationCheckpoint(
        run_id=run_id,
        state=state,
        source_id=source_id,
        raw_content=document.content,
        reason=reason,
        requires_human_review=requires_human_review,
        documentation_update_allowed=documentation_update_allowed,
    )


def validate_document_for_sync(
    document: RepositoryDocument,
    *,
    run_id: str,
    checkpoint_store: CheckpointStore | None = None,
    raise_on_invalid: bool = False,
) -> DocumentValidationResult:
    """Reject empty or malformed documents before synchronization can proceed."""
    if not run_id:
        raise ValueError("run_id is required")

    if document.content is None or not document.content:
        reason = "Empty policy document: no raw bytes were provided"
        checkpoint = _checkpoint_for(
            run_id=run_id,
            document=document,
            state=SYNC_FAILED,
            reason=reason,
            requires_human_review=True,
            documentation_update_allowed=False,
        )
        if checkpoint_store is not None:
            checkpoint_store.record(checkpoint)
        if raise_on_invalid:
            raise EmptyOrInvalidDocumentError(reason)
        return DocumentValidationResult(
            document=document,
            is_valid=False,
            reason=reason,
            checkpoint=checkpoint,
            requires_human_review=True,
            documentation_update_allowed=False,
        )

    try:
        parsed = read_source_document(document)
    except Exception as exc:  # pragma: no cover - defensive failure path
        reason = f"Malformed policy document: {exc}"
        checkpoint = _checkpoint_for(
            run_id=run_id,
            document=document,
            state=SYNC_FAILED,
            reason=reason,
            requires_human_review=True,
            documentation_update_allowed=False,
        )
        if checkpoint_store is not None:
            checkpoint_store.record(checkpoint)
        if raise_on_invalid:
            raise EmptyOrInvalidDocumentError(reason) from exc
        return DocumentValidationResult(
            document=document,
            is_valid=False,
            reason=reason,
            checkpoint=checkpoint,
            requires_human_review=True,
            documentation_update_allowed=False,
        )

    if not _document_has_content(parsed.html_content):
        reason = "Empty or contentless policy document: the source body contains no visible text"
        checkpoint = _checkpoint_for(
            run_id=run_id,
            document=document,
            state=SYNC_FAILED,
            reason=reason,
            requires_human_review=True,
            documentation_update_allowed=False,
        )
        if checkpoint_store is not None:
            checkpoint_store.record(checkpoint)
        if raise_on_invalid:
            raise EmptyOrInvalidDocumentError(reason)
        return DocumentValidationResult(
            document=document,
            is_valid=False,
            reason=reason,
            checkpoint=checkpoint,
            requires_human_review=True,
            documentation_update_allowed=False,
        )

    checkpoint = _checkpoint_for(
        run_id=run_id,
        document=document,
        state="SYNC_INGESTED",
        reason="Document passed content validation",
        requires_human_review=False,
        documentation_update_allowed=True,
    )
    if checkpoint_store is not None:
        checkpoint_store.record(checkpoint)
    return DocumentValidationResult(
        document=document,
        is_valid=True,
        reason="Document passed content validation",
        checkpoint=checkpoint,
        requires_human_review=False,
        documentation_update_allowed=True,
    )
