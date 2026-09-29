from dataclasses import dataclass


SYNC_FAILED = "SYNC_FAILED"


@dataclass(frozen=True)
class SynchronizationCheckpoint:
    run_id: str
    state: str
    source_id: str
    raw_content: bytes
    reason: str
    requires_human_review: bool
    documentation_update_allowed: bool


class CheckpointStore:
    """Minimal immutable checkpoint store used by the T08 validation gate."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, SynchronizationCheckpoint] = {}

    def record(self, checkpoint: SynchronizationCheckpoint) -> None:
        if checkpoint.run_id in self._checkpoints:
            raise ValueError(f"Checkpoint already exists: {checkpoint.run_id}")
        self._checkpoints[checkpoint.run_id] = checkpoint

    def get(self, run_id: str) -> SynchronizationCheckpoint | None:
        return self._checkpoints.get(run_id)
