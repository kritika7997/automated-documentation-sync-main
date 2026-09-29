from automated_documentation_sync.domain.policy_model import CanonicalPolicyModel

from .repositories import InMemoryRepository


class PolicyRepository:
    """Provider-neutral persistence seam for immutable canonical policy records."""

    def __init__(self) -> None:
        self._records = InMemoryRepository[CanonicalPolicyModel]()

    def add(self, policy: CanonicalPolicyModel) -> None:
        self._records.add(policy.policy_version_id, policy)

    def get(self, policy_version_id: str) -> CanonicalPolicyModel | None:
        return self._records.get(policy_version_id)


__all__ = ["PolicyRepository"]