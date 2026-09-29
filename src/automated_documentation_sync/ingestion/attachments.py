from dataclasses import dataclass

from .contracts import RepositoryDocument
from .mhtml_reader import EmbeddedResource, ParsedSourceDocument, read_source_document


@dataclass(frozen=True)
class SourcePackage:
    document: RepositoryDocument
    parsed: ParsedSourceDocument
    attachments: tuple[EmbeddedResource, ...]


def extract_source_package(document: RepositoryDocument) -> SourcePackage:
    """Return decoded HTML and embedded resources while retaining raw input."""
    parsed = read_source_document(document)
    return SourcePackage(document=document, parsed=parsed, attachments=parsed.resources)
