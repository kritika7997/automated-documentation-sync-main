from pathlib import Path


FIXTURES = Path(__file__).parent / "fixtures"


def test_policy_fixtures_are_available():
    assert (FIXTURES / "empty_policy.html").read_text()
    assert (FIXTURES / "sample_policy.html").read_text()
