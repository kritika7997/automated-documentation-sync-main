from __future__ import annotations

import re
from dataclasses import dataclass, replace
from html.parser import HTMLParser
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.domain.faq import FAQEntry
from automated_documentation_sync.ingestion.contracts import RepositoryDocument
from automated_documentation_sync.ingestion.mhtml_reader import EmbeddedResource, read_source_document


@dataclass(frozen=True)
class Section:
    heading: str
    body: str
    source_location: SourceLocation


@dataclass(frozen=True)
class Paragraph:
    text: str
    source_location: SourceLocation


@dataclass(frozen=True)
class ListItem:
    text: str
    source_location: SourceLocation


@dataclass(frozen=True)
class TableRow:
    cells: tuple[str, ...]
    source_location: SourceLocation


@dataclass(frozen=True)
class Table:
    rows: tuple[TableRow, ...]
    source_location: SourceLocation


@dataclass(frozen=True)
class ParsedPolicyDocument:
    raw_content: bytes
    normalized_text: str
    sections: tuple[Section, ...]
    paragraphs: tuple[Paragraph, ...]
    lists: tuple[ListItem, ...]
    tables: tuple[Table, ...]
    links: tuple[str, ...]
    email_addresses: tuple[str, ...]
    effective_dates: tuple[str, ...]
    attachments: tuple[EmbeddedResource, ...]
    unresolved_references: tuple[str, ...]
    faq_entries: tuple[FAQEntry, ...] = ()
    source_location: SourceLocation | None = None


class _PolicyHTMLParser(HTMLParser):
    def __init__(self, document_version_id: str) -> None:
        super().__init__(convert_charrefs=True)
        self._document_version_id = document_version_id
        self._text_parts: list[str] = []
        self._headings: list[str] = []
        self._sections: list[Section] = []
        self._paragraphs: list[Paragraph] = []
        self._lists: list[ListItem] = []
        self._rows: list[TableRow] = []
        self._tables: list[Table] = []
        self._links: list[str] = []
        self._emails: list[str] = []
        self._effective_dates: list[str] = []
        self._current_heading: str | None = None
        self._current_section_name: str | None = None
        self._current_section_text: list[str] = []
        self._current_section_index: int | None = None
        self._current_list: list[str] = []
        self._current_row: list[str] = []
        self._current_paragraph: list[str] = []
        self._in_heading = False
        self._in_list_item = False
        self._in_paragraph = False

    def _location(self, section: str, locator: str) -> SourceLocation:
        return SourceLocation(
            document_version_id=self._document_version_id,
            section=section,
            locator=locator,
        )

    def _append_section_text(self, text: str) -> None:
        self._current_section_text.append(text)
        if self._current_section_index is not None:
            section = self._sections[self._current_section_index]
            self._sections[self._current_section_index] = replace(
                section,
                body=" ".join(self._current_section_text),
            )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._in_heading = True
            self._current_heading = ""
        if tag == "a":
            for name, value in attrs:
                if name.lower() == "href" and value:
                    self._links.append(value)
        if tag == "p":
            self._in_paragraph = True
            self._current_paragraph = []
        if tag == "li":
            self._current_list.append("")
            self._in_list_item = True
        if tag == "tr":
            self._current_row = []
        if tag == "table":
            self._current_row = []
        if tag in {"td", "th"}:
            self._current_row.append("")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self._current_heading:
            heading = " ".join(self._current_heading.split())
            self._headings.append(heading)
            self._sections.append(
                Section(
                    heading=heading,
                    body="",
                    source_location=self._location(heading, heading),
                )
            )
            self._current_section_index = len(self._sections) - 1
            self._current_section_name = heading
            self._current_section_text = []
            self._current_heading = heading
            self._in_heading = False
        elif tag == "p":
            text = " ".join(self._current_paragraph).strip()
            if text:
                section_name = self._current_section_name or self._current_heading or "body"
                self._paragraphs.append(Paragraph(text=text, source_location=self._location(section_name, text[:60])))
                self._append_section_text(text)
                self._text_parts.append(text)
            self._current_paragraph = []
            self._in_paragraph = False
        elif tag == "li":
            item_text = " ".join(self._current_list).strip()
            if item_text:
                section_name = self._current_section_name or self._current_heading or "body"
                self._lists.append(ListItem(text=item_text, source_location=self._location(section_name, item_text[:60])))
                self._append_section_text(item_text)
                self._text_parts.append(item_text)
            self._current_list = []
            self._in_list_item = False
        elif tag == "tr":
            if self._current_row:
                row = TableRow(cells=tuple(cell.strip() for cell in self._current_row if cell.strip()), source_location=self._location(self._current_heading or "body", "row"))
                self._rows.append(row)
                self._append_section_text(" ".join(row.cells))
            self._current_row = []
        elif tag == "table":
            if self._rows:
                table = Table(rows=tuple(self._rows), source_location=self._location(self._current_heading or "body", "table"))
                self._tables.append(table)
                self._text_parts.append(" ".join(cell for row in self._rows for cell in row.cells))
                self._rows = []

    def handle_data(self, data: str) -> None:
        if self._in_heading:
            self._current_heading = f"{self._current_heading or ''}{data}"
        elif self._in_paragraph:
            self._current_paragraph.append(data)
        elif self._in_list_item and self._current_list:
            self._current_list[-1] += data
        else:
            self._text_parts.append(data)

        if data and re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", data):
            self._emails.extend(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", data))

        for match in re.finditer(r"\b(?:0?[1-9]|[12][0-9]|3[01])\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b", data, re.IGNORECASE):
            self._effective_dates.append(match.group(0))

        if self._current_row:
            self._current_row[-1] = f"{self._current_row[-1]}{data}"

    def result(
        self,
        raw_content: bytes,
        attachments: tuple[EmbeddedResource, ...],
        unresolved_references: tuple[str, ...],
    ) -> ParsedPolicyDocument:
        normalized = " ".join(part.strip() for part in self._text_parts if part and part.strip())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return ParsedPolicyDocument(
            raw_content=raw_content,
            normalized_text=normalized,
            sections=tuple(self._sections),
            paragraphs=tuple(self._paragraphs),
            lists=tuple(self._lists),
            tables=tuple(self._tables),
            links=tuple(dict.fromkeys(self._links)),
            email_addresses=tuple(dict.fromkeys(self._emails)),
            effective_dates=tuple(dict.fromkeys(self._effective_dates)),
            attachments=attachments,
            unresolved_references=unresolved_references,
            source_location=self._location("policy", "document"),
        )


def parse_policy_document(document: RepositoryDocument) -> ParsedPolicyDocument:
    parsed_source = read_source_document(document)
    parser = _PolicyHTMLParser(document.commit_sha)
    parser.feed(parsed_source.html_content.decode("utf-8", errors="replace"))
    parser.close()
    parsed = parser.result(
        document.content,
        parsed_source.resources,
        parsed_source.unresolved_references,
    )
    from automated_documentation_sync.parsing.faq_parser import extract_faq_entries

    return replace(parsed, faq_entries=extract_faq_entries(parsed))


class PolicyParser:
    def parse(self, document: RepositoryDocument) -> ParsedPolicyDocument:
        return parse_policy_document(document)
