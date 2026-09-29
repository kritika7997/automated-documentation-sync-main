from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PolicyDocumentRecord:
    document_id: str
    content_hash: str
    received_at: datetime
    media_type: str
    raw_content: bytes


@dataclass(frozen=True)
class PolicyVersionRecord:
    version_id: str
    document_id: str
    content_hash: str
    predecessor_id: str | None = None
    effective_date: str | None = None


@dataclass(frozen=True)
class CheckpointRecord:
    run_id: str
    state: str
    change_set_id: str | None = None
    artifact_hash: str | None = None
