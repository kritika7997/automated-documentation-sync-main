from automated_documentation_sync.changes.conflicts import ConflictKind, detect_conflicts
from automated_documentation_sync.domain.policy_model import build_canonical_policy
from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser


def canonical(html: str):
    document = RepositoryDocument(
        content=html.encode(),
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha="canonical-unit-v1",
        media_type="text/html",
    )
    return build_canonical_policy(PolicyParser().parse(document))


def test_canonical_model_preserves_raw_content_hash_and_normalized_statements():
    raw = "<html><body><h1>Policy</h1><p>  Policy   wording. </p></body></html>"

    model = canonical(raw)

    assert model.raw_content == raw.encode()
    assert model.raw_content_hash
    assert model.normalized_text
    assert model.statements[0].raw_text == "Policy   wording."
    assert model.statements[0].normalized_text == "Policy wording."
    assert model.statements[0].source_location.document_version_id == "canonical-unit-v1"


def test_conflicting_formula_content_is_preserved_and_flagged_for_review():
    model = canonical(
        "<html><body><h1>Policy</h1>"
        "<p>Hourly wage = Wage Salary / 365 / 8 hours.</p>"
        "<p>Hourly wage = Wage Salary / 365 / 9 hours.</p>"
        "</body></html>"
    )

    conflicts = detect_conflicts(model)

    formula_conflict = next(conflict for conflict in conflicts if conflict.kind is ConflictKind.FORMULA)
    assert len(formula_conflict.values) == 2
    assert formula_conflict.requires_human_review is True