from dataclasses import dataclass

from .classifications import Classification
from .models import SourceLocation


@dataclass(frozen=True)
class FAQEntry:
    question: str
    answer: str | None
    classification: Classification
    source_location: SourceLocation
    email_addresses: tuple[str, ...] = ()
    incomplete: bool = False


__all__ = ["FAQEntry"]