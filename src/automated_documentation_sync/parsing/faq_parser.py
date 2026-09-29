from __future__ import annotations

import re
from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.faq import FAQEntry
from automated_documentation_sync.parsing.policy_parser import Paragraph, ParsedPolicyDocument


_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _is_faq_section(section: str) -> bool:
    normalized = section.casefold()
    return "faq" in normalized or "frequently asked" in normalized


def _split_question_answer(text: str) -> tuple[str, str | None]:
    question_end = text.find("?")
    if question_end < 0:
        return text.strip(), None

    question = text[: question_end + 1].strip()
    answer = text[question_end + 1 :].strip() or None
    return question, answer


def _entry_from_paragraph(paragraph: Paragraph) -> FAQEntry:
    question, answer = _split_question_answer(paragraph.text)
    emails = tuple(dict.fromkeys(_EMAIL_PATTERN.findall(paragraph.text)))
    return FAQEntry(
        question=question,
        answer=answer,
        classification=Classification.SOURCE_FAQ,
        source_location=paragraph.source_location,
        email_addresses=emails,
        incomplete=answer is None,
    )


def extract_faq_entries(document: ParsedPolicyDocument) -> tuple[FAQEntry, ...]:
    """Extract FAQ paragraphs without merging them into source-policy records."""
    return tuple(
        _entry_from_paragraph(paragraph)
        for paragraph in document.paragraphs
        if _is_faq_section(paragraph.source_location.section)
    )


__all__ = ["extract_faq_entries"]