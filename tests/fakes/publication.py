class FakePublicationRepository:
    """Provider-neutral fake used only by publication-gate integration tests."""

    def __init__(self) -> None:
        self.published: dict[str, str] = {}

    def publish(self, *, approved: bool, artifact_id: str, content_hash: str) -> None:
        if not approved:
            raise PermissionError("Publication requires approved review")
        if artifact_id in self.published:
            raise ValueError("Duplicate publication")
        self.published[artifact_id] = content_hash