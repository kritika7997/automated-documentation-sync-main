from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from automated_documentation_sync.domain.policy_model import CanonicalPolicyModel


PARSER_VERSION = "policy-parser-v1"


@dataclass(frozen=True)
class PolicyVersion:
    version_id: str
    source_hash: str
    parser_version: str
    received_at: datetime
    effective_date: str | None = None
    predecessor_id: str | None = None

    @property
    def supersedes_id(self) -> str | None:
        return self.predecessor_id


def create_policy_version(
    policy: CanonicalPolicyModel,
    *,
    received_at: datetime,
    predecessor_id: str | None = None,
    parser_version: str = PARSER_VERSION,
) -> PolicyVersion:
    if not policy.policy_version_id:
        raise ValueError("Canonical policy version ID is required")
    if not parser_version:
        raise ValueError("Parser version is required")
    return PolicyVersion(
        version_id=policy.policy_version_id,
        source_hash=policy.raw_content_hash,
        parser_version=parser_version,
        received_at=received_at,
        effective_date=policy.dates[0] if policy.dates else None,
        predecessor_id=predecessor_id,
    )


__all__ = ["PARSER_VERSION", "PolicyVersion", "create_policy_version"]