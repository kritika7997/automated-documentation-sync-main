from dataclasses import dataclass
from email import policy
from email.message import Message
from email.parser import BytesParser
from html.parser import HTMLParser
from typing import Iterable

from .contracts import RepositoryDocument


@dataclass(frozen=True)
class EmbeddedResource:
    content: bytes
    media_type: str
    content_location: str | None
    content_id: str | None
    filename: str | None


@dataclass(frozen=True)
class ParsedSourceDocument:
    raw_content: bytes
    html_content: bytes
    html_media_type: str
    resources: tuple[EmbeddedResource, ...]
    unresolved_references: tuple[str, ...]


class _ReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name.lower() in {"href", "src"} and value:
                self.references.append(value)


def _decode_part(part: Message) -> bytes:
    payload = part.get_payload(decode=True)
    if payload is None:
        return b""
    return payload


def _resource_from_part(part: Message) -> EmbeddedResource:
    return EmbeddedResource(
        content=_decode_part(part),
        media_type=part.get_content_type(),
        content_location=part.get("Content-Location"),
        content_id=part.get("Content-ID"),
        filename=part.get_filename(),
    )


def _iter_parts(message: Message) -> Iterable[Message]:
    if message.is_multipart():
        yield from message.walk()
    else:
        yield message


def _unresolved_references(html_content: bytes, resources: tuple[EmbeddedResource, ...]) -> tuple[str, ...]:
    parser = _ReferenceParser()
    try:
        parser.feed(html_content.decode("utf-8", errors="replace"))
    except Exception:
        return tuple(parser.references)

    known_locations = {resource.content_location for resource in resources if resource.content_location}
    known_ids = {
        resource.content_id.strip("<>")
        for resource in resources
        if resource.content_id
    }
    return tuple(
        reference
        for reference in parser.references
        if reference not in known_locations
        and reference.removeprefix("cid:").strip("<>") not in known_ids
        and not reference.startswith(("http://", "https://", "mailto:", "#"))
    )


def read_source_document(document: RepositoryDocument) -> ParsedSourceDocument:
    """Decode a raw repository document without validating policy semantics."""
    raw_content = document.content
    if document.media_type in {"multipart/related", "message/rfc822"} or b"boundary=" in raw_content[:4096].lower():
        message = BytesParser(policy=policy.default).parsebytes(raw_content)
    else:
        return ParsedSourceDocument(
            raw_content=raw_content,
            html_content=raw_content,
            html_media_type=document.media_type or "text/html",
            resources=(),
            unresolved_references=(),
        )

    html_content = b""
    html_media_type = "text/html"
    resources: list[EmbeddedResource] = []
    for part in _iter_parts(message):
        if part.is_multipart():
            continue
        payload = _decode_part(part)
        if part.get_content_type() == "text/html" and not html_content:
            html_content = payload
            html_media_type = part.get_content_type()
            continue
        resources.append(_resource_from_part(part))

    resource_tuple = tuple(resources)
    return ParsedSourceDocument(
        raw_content=raw_content,
        html_content=html_content,
        html_media_type=html_media_type,
        resources=resource_tuple,
        unresolved_references=_unresolved_references(html_content, resource_tuple),
    )
