from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.ingestion.mhtml_reader import EmbeddedResource
from automated_documentation_sync.parsing.policy_parser import (
    ParsedPolicyDocument,
    Table,
)


@dataclass(frozen=True)
class CanonicalStatement:
    statement_id: str
    raw_text: str
    normalized_text: str
    classification: Classification
    source_location: SourceLocation
    content_hash: str
    conflict_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalFAQEntry:
    question: str
    answer: str | None
    classification: Classification
    source_location: SourceLocation
    content_hash: str
    email_addresses: tuple[str, ...] = ()
    incomplete: bool = False
    conflict_flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalAttachment:
    content: bytes
    media_type: str
    content_location: str | None
    content_id: str | None
    filename: str | None
    content_hash: str


@dataclass(frozen=True)
class CanonicalPolicyModel:
    policy_version_id: str
    raw_content: bytes
    raw_content_hash: str
    normalized_text: str
    statements: tuple[CanonicalStatement, ...]
    faq_entries: tuple[CanonicalFAQEntry, ...]
    tables: tuple[Table, ...]
    formulas: tuple[str, ...]
    thresholds: tuple[str, ...]
    contacts: tuple[str, ...]
    dates: tuple[str, ...]
    attachments: tuple[CanonicalAttachment, ...]
    conflict_flags: tuple[str, ...] = ()


def _content_hash(value: bytes | str) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _normalized(text: str) -> str:
    return " ".join(text.split())


def _statement_id(location: SourceLocation, text: str) -> str:
    return _content_hash(f"{location.document_version_id}:{location.section}:{location.locator}:{text}")


def _policy_statements(document: ParsedPolicyDocument) -> tuple[CanonicalStatement, ...]:
    records: list[CanonicalStatement] = []
    source_items = [*document.paragraphs, *document.lists]
    for item in source_items:
        section = item.source_location.section.casefold()
        if "faq" in section or "frequently asked" in section:
            continue
        text = item.text
        records.append(
            CanonicalStatement(
                statement_id=_statement_id(item.source_location, text),
                raw_text=text,
                normalized_text=_normalized(text),
                classification=Classification.SOURCE_POLICY,
                source_location=item.source_location,
                content_hash=_content_hash(text),
            )
        )
    return tuple(records)


def _faq_entries(document: ParsedPolicyDocument) -> tuple[CanonicalFAQEntry, ...]:
    return tuple(
        CanonicalFAQEntry(
            question=entry.question,
            answer=entry.answer,
            classification=entry.classification,
            source_location=entry.source_location,
            content_hash=_content_hash(f"{entry.question}\n{entry.answer or ''}"),
            email_addresses=entry.email_addresses,
            incomplete=entry.incomplete,
        )
        for entry in document.faq_entries
    )


def _candidate_values(document: ParsedPolicyDocument) -> tuple[tuple[str, ...], tuple[str, ...]]:
    texts = [statement.raw_text for statement in _policy_statements(document)]
    formulas = tuple(text for text in texts if "=" in text)
    thresholds = tuple(
        text
        for text in texts
        if re.search(r"\b\d+(?:\.\d+)?\s*(?:hours?|days?|times?|x)\b", text, re.IGNORECASE)
    )
    return formulas, thresholds


def build_canonical_policy(document: ParsedPolicyDocument) -> CanonicalPolicyModel:
    """Build an immutable canonical record without resolving policy conflicts."""
    formulas, thresholds = _candidate_values(document)
    attachments = tuple(
        CanonicalAttachment(
            content=resource.content,
            media_type=resource.media_type,
            content_location=resource.content_location,
            content_id=resource.content_id,
            filename=resource.filename,
            content_hash=_content_hash(resource.content),
        )
        for resource in document.attachments
    )
    return CanonicalPolicyModel(
        policy_version_id=document.source_location.document_version_id if document.source_location else "",
        raw_content=document.raw_content,
        raw_content_hash=_content_hash(document.raw_content),
        normalized_text=document.normalized_text,
        statements=_policy_statements(document),
        faq_entries=_faq_entries(document),
        tables=document.tables,
        formulas=formulas,
        thresholds=thresholds,
        contacts=document.email_addresses,
        dates=document.effective_dates,
        attachments=attachments,
    )


__all__ = [
    "CanonicalAttachment",
    "CanonicalFAQEntry",
    "CanonicalPolicyModel",
    "CanonicalStatement",
    "build_canonical_policy",
]