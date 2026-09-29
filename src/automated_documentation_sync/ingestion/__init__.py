from .contracts import (
    InvalidSourceDocument,
    PolicySource,
    RepositoryDocument,
    SourceRepositoryConfiguration,
    SourceAdapterError,
    SourceDocumentNotFound,
    SourceRepositoryUnavailable,
)
from .attachments import SourcePackage, extract_source_package
from .github_source_adapter import GitHubPolicySourceAdapter
from .mhtml_reader import EmbeddedResource, ParsedSourceDocument, read_source_document
from .validation import (
    DocumentValidationResult,
    EmptyOrInvalidDocumentError,
    validate_document_for_sync,
)

__all__ = [
    "GitHubPolicySourceAdapter",
    "InvalidSourceDocument",
    "PolicySource",
    "RepositoryDocument",
    "SourceRepositoryConfiguration",
    "SourceAdapterError",
    "SourceDocumentNotFound",
    "SourceRepositoryUnavailable",
    "EmbeddedResource",
    "ParsedSourceDocument",
    "SourcePackage",
    "DocumentValidationResult",
    "EmptyOrInvalidDocumentError",
    "extract_source_package",
    "read_source_document",
    "validate_document_for_sync",
]
