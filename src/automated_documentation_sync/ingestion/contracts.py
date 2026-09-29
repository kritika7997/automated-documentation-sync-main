from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class SourceAdapterError(RuntimeError):
    """Base error for safe source-adapter failures."""


class SourceDocumentNotFound(SourceAdapterError):
    """Raised when the configured policy path is absent at the requested ref."""


class SourceRepositoryUnavailable(SourceAdapterError):
    """Raised when the source repository cannot be queried safely."""


class InvalidSourceDocument(SourceAdapterError):
    """Raised when a repository response lacks required source metadata."""


@dataclass(frozen=True)
class SourceRepositoryConfiguration:
    """Provider-neutral source configuration with no credential material."""

    owner: str
    name: str
    document_path: str
    ref: str

    @property
    def repository(self) -> str:
        return f"{self.owner}/{self.name}"

    def __post_init__(self) -> None:
        if not all((self.owner, self.name, self.document_path, self.ref)):
            raise ValueError("Source repository owner, name, path, and ref are required")


@dataclass(frozen=True)
class RepositoryDocument:
    content: bytes
    repository: str
    path: str
    ref: str
    commit_sha: str
    media_type: str | None = None

    def __post_init__(self) -> None:
        if self.content is None or not self.repository or not self.path or not self.ref or not self.commit_sha:
            raise ValueError("Repository document provenance metadata are required")


@dataclass(frozen=True)
class PolicySource:
    source_id: str
    content: bytes
    content_hash: str
    repository: str
    path: str
    ref: str
    commit_sha: str
    media_type: str | None
    fetched_at: datetime


class RepositoryDocumentClient(Protocol):
    def get_document(self, repository: str, path: str, ref: str) -> RepositoryDocument | None:
        """Return the immutable document at ref, or None when it is absent."""
