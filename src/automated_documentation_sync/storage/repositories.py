from typing import Generic, TypeVar


Record = TypeVar("Record")


class DuplicateRecordError(ValueError):
    """Raised when an immutable record identifier already exists."""


class InMemoryRepository(Generic[Record]):
    """Small persistence seam used until the approved database is selected."""

    def __init__(self) -> None:
        self._records: dict[str, Record] = {}

    def add(self, record_id: str, record: Record) -> None:
        if record_id in self._records:
            raise DuplicateRecordError(record_id)
        self._records[record_id] = record

    def get(self, record_id: str) -> Record | None:
        return self._records.get(record_id)
