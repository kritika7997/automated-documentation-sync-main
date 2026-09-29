from automated_documentation_sync.domain.policy_model import build_canonical_policy
from automated_documentation_sync.ingestion import RepositoryDocument
from automated_documentation_sync.parsing import PolicyParser
from automated_documentation_sync.changes.detector import ChangeType, compare_policy_versions


def policy(content: str, version: str):
    document = RepositoryDocument(
        content=content.encode(),
        repository="org/policy-repository",
        path="policies/overtime-policy.html",
        ref="main",
        commit_sha=version,
        media_type="text/html",
    )
    return build_canonical_policy(PolicyParser().parse(document))


def test_detector_reports_added_removed_and_modified_statements_with_provenance():
    previous = policy("<html><body><h1>Policy</h1><p>Kept rule.</p><p>Removed rule.</p></body></html>", "v1")
    current = policy("<html><body><h1>Policy</h1><p>Kept rule.</p><p>Added rule.</p><p>New rule.</p></body></html>", "v2")

    changes = compare_policy_versions(previous, current, affected_requirement_ids=("FR-017",))

    statement_types = {change.change_type for change in changes if change.category == "statement"}
    assert ChangeType.MODIFIED in statement_types
    assert ChangeType.ADDED in statement_types
    removed = compare_policy_versions(
        policy("<html><body><h1>Policy</h1><p>Kept rule.</p><p>Removed rule.</p></body></html>", "v1b"),
        policy("<html><body><h1>Policy</h1><p>Kept rule.</p></body></html>", "v2b"),
    )
    assert any(change.change_type is ChangeType.REMOVED for change in removed if change.category == "statement")
    assert all(change.source_locations for change in changes)
    assert all(change.affected_requirement_ids == ("FR-017",) for change in changes)


def test_detector_compares_tables_faq_numeric_and_contact_values():
    previous = policy(
        "<html><body><h1>Policy</h1><p>Threshold is 6 hours.</p><p>Contact old@example.com.</p>"
        "<h2>FAQ</h2><p>What is the rate? Two times.</p><table><tr><td>V1</td></tr></table></body></html>",
        "v1",
    )
    current = policy(
        "<html><body><h1>Policy</h1><p>Threshold is 9 hours.</p><p>Contact new@example.com.</p>"
        "<h2>FAQ</h2><p>What is the rate? Three times.</p><table><tr><td>V2</td></tr></table></body></html>",
        "v2",
    )

    changes = compare_policy_versions(previous, current)
    categories = {change.category for change in changes}

    assert {"threshold", "contact", "faq", "table"}.issubset(categories)


def test_detector_marks_whitespace_only_statement_change_as_formatting_only():
    previous = policy("<html><body><h1>Policy</h1><p>Same   rule.</p></body></html>", "v1")
    current = policy("<html><body><h1>Policy</h1><p>Same rule.</p></body></html>", "v2")

    changes = compare_policy_versions(previous, current)

    statement_changes = [change for change in changes if change.category == "statement"]
    assert len(statement_changes) == 1
    assert statement_changes[0].change_type is ChangeType.FORMATTING_ONLY