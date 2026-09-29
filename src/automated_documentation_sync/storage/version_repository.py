from automated_documentation_sync.versioning.version_registry import PolicyVersion

from .repositories import InMemoryRepository


class DuplicateVersionHashError(ValueError):
    """Raised when source content is registered more than once."""


class InvalidVersionLineageError(ValueError):
    """Raised when a version predecessor relationship is invalid."""


class VersionRepository:
    """Provider-neutral immutable storage for policy versions."""

    def __init__(self) -> None:
        self._records = InMemoryRepository[PolicyVersion]()
        self._hashes: dict[str, str] = {}
        self._successors: dict[str, str] = {}

    def add(self, version: PolicyVersion) -> None:
        if version.source_hash in self._hashes:
            raise DuplicateVersionHashError(version.source_hash)
        if version.predecessor_id is not None:
            if self.get(version.predecessor_id) is None:
                raise InvalidVersionLineageError(version.predecessor_id)
            if version.predecessor_id in self._successors:
                raise InvalidVersionLineageError(version.predecessor_id)
        self._records.add(version.version_id, version)
        self._hashes[version.source_hash] = version.version_id
        if version.predecessor_id is not None:
            self._successors[version.predecessor_id] = version.version_id

    def get(self, version_id: str) -> PolicyVersion | None:
        return self._records.get(version_id)

    def get_successor(self, version_id: str) -> PolicyVersion | None:
        successor_id = self._successors.get(version_id)
        return self.get(successor_id) if successor_id is not None else None


__all__ = [
    "DuplicateVersionHashError",
    "InvalidVersionLineageError",
    "VersionRepository",
]