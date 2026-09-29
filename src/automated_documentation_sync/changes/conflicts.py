from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from enum import StrEnum

from automated_documentation_sync.domain.classifications import Classification
from automated_documentation_sync.domain.models import SourceLocation
from automated_documentation_sync.domain.policy_model import CanonicalPolicyModel


class ConflictKind(StrEnum):
    FORMULA = "formula"
    THRESHOLD = "threshold"
    CONTACT = "contact"
    FAQ_POLICY = "faq_policy"


class ReviewOutcome(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"


@dataclass(frozen=True)
class ConflictRecord:
    conflict_id: str
    kind: ConflictKind
    values: tuple[str, ...]
    source_locations: tuple[SourceLocation, ...]
    classifications: tuple[Classification, ...]
    review_outcome: ReviewOutcome | None = None

    @property
    def requires_human_review(self) -> bool:
        return self.review_outcome is None

    @property
    def is_authoritative(self) -> bool:
        return self.review_outcome is not None

    @property
    def is_finalizable(self) -> bool:
        return self.review_outcome is not None

    def with_review_outcome(self, outcome: ReviewOutcome) -> ConflictRecord:
        return replace(self, review_outcome=outcome)


def _conflict_id(kind: ConflictKind, values: tuple[str, ...]) -> str:
    payload = f"{kind.value}:{'|'.join(values)}".encode()
    return hashlib.sha256(payload).hexdigest()


def _record(
    kind: ConflictKind,
    values: tuple[str, ...],
    locations: tuple[SourceLocation, ...],
    classifications: tuple[Classification, ...],
) -> ConflictRecord:
    return ConflictRecord(
        conflict_id=_conflict_id(kind, values),
        kind=kind,
        values=values,
        source_locations=locations,
        classifications=classifications,
    )


def _distinct(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def detect_conflicts(policy: CanonicalPolicyModel) -> tuple[ConflictRecord, ...]:
    """Detect contradictions while retaining every source value and location."""
    conflicts: list[ConflictRecord] = []
    if len(_distinct(policy.formulas)) > 1:
        conflicts.append(
            _record(
                ConflictKind.FORMULA,
                _distinct(policy.formulas),
                tuple(statement.source_location for statement in policy.statements if "=" in statement.raw_text),
                tuple(statement.classification for statement in policy.statements if "=" in statement.raw_text),
            )
        )
    if len(_distinct(policy.thresholds)) > 1:
        conflicts.append(
            _record(
                ConflictKind.THRESHOLD,
                _distinct(policy.thresholds),
                tuple(statement.source_location for statement in policy.statements if statement.raw_text in policy.thresholds),
                tuple(statement.classification for statement in policy.statements if statement.raw_text in policy.thresholds),
            )
        )

    faq_contacts = tuple(email for entry in policy.faq_entries for email in entry.email_addresses)
    policy_contacts = tuple(
        email
        for email in policy.contacts
        if email not in faq_contacts
    )
    if faq_contacts and policy_contacts and set(faq_contacts) != set(policy_contacts):
        locations = tuple(entry.source_location for entry in policy.faq_entries if entry.email_addresses)
        locations += tuple(statement.source_location for statement in policy.statements if any(email in statement.raw_text for email in policy_contacts))
        conflicts.append(
            _record(
                ConflictKind.CONTACT,
                _distinct(faq_contacts + policy_contacts),
                locations,
                tuple(Classification.SOURCE_FAQ for _ in faq_contacts)
                + tuple(Classification.SOURCE_POLICY for _ in policy_contacts),
            )
        )

    policy_values = tuple(statement.raw_text for statement in policy.statements)
    for entry in policy.faq_entries:
        faq_text = f"{entry.question} {entry.answer or ''}"
        faq_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\s*(?:hours?|days?|times?|x)\b", faq_text, re.IGNORECASE))
        for policy_text in policy_values:
            policy_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\s*(?:hours?|days?|times?|x)\b", policy_text, re.IGNORECASE))
            if faq_numbers and policy_numbers and faq_numbers != policy_numbers:
                conflicts.append(
                    _record(
                        ConflictKind.FAQ_POLICY,
                        (policy_text, faq_text),
                        (entry.source_location,),
                        (Classification.SOURCE_POLICY, Classification.SOURCE_FAQ),
                    )
                )
                break
    return tuple(conflicts)


__all__ = ["ConflictKind", "ConflictRecord", "ReviewOutcome", "detect_conflicts"]