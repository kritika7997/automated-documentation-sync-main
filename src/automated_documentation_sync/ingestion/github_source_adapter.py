import hashlib
from datetime import datetime, timezone

from .contracts import (
    InvalidSourceDocument,
    PolicySource,
    RepositoryDocument,
    RepositoryDocumentClient,
    SourceRepositoryConfiguration,
    SourceDocumentNotFound,
    SourceRepositoryUnavailable,
)


class GitHubPolicySourceAdapter:
    """Retrieve a policy document from an injected GitHub repository client."""

    def __init__(self, client: RepositoryDocumentClient, configuration: SourceRepositoryConfiguration) -> None:
        self._client = client
        self._configuration = configuration

    def retrieve(self) -> PolicySource:
        try:
            document = self._client.get_document(
                self._configuration.repository,
                self._configuration.document_path,
                self._configuration.ref,
            )
        except Exception as error:
            raise SourceRepositoryUnavailable("Unable to retrieve policy source") from error

        if document is None:
            raise SourceDocumentNotFound(
                f"Policy document not found at {self._configuration.repository}:"
                f"{self._configuration.document_path}@{self._configuration.ref}"
            )

        if not isinstance(document, RepositoryDocument):
            raise InvalidSourceDocument("Repository returned an invalid policy document response")

        content_hash = hashlib.sha256(document.content).hexdigest()
        source_id = f"github:{document.repository}:{document.path}@{document.ref}:{document.commit_sha}"
        return PolicySource(
            source_id=source_id,
            content=document.content,
            content_hash=content_hash,
            repository=document.repository,
            path=document.path,
            ref=document.ref,
            commit_sha=document.commit_sha,
            media_type=document.media_type,
            fetched_at=datetime.now(timezone.utc),
        )
