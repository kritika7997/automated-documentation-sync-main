from automated_documentation_sync.generation.artifacts import ArtifactSnapshot

from .repositories import InMemoryRepository


class ArtifactRepository:
    """Provider-neutral immutable storage for review artifact snapshots."""

    def __init__(self) -> None:
        self._records = InMemoryRepository[ArtifactSnapshot]()

    def add(self, artifact: ArtifactSnapshot) -> None:
        self._records.add(artifact.artifact_id, artifact)

    def get(self, artifact_id: str) -> ArtifactSnapshot | None:
        return self._records.get(artifact_id)


__all__ = ["ArtifactRepository"]