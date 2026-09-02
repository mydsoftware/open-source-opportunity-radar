"""Backward-compatibility smoke tests for the original scan.score signature."""
from scripts import scan


def test_license_scores_are_ordered():
    repo = {
        "stargazers_count": 10000,
        "forks_count": 500,
        "open_issues_count": 20,
        "pushed_at": "2026-09-01T00:00:00Z",
        "name": "ai-agent",
        "description": "AI agent",
    }
    mit = scan.score(repo, "AI", 100)[0]
    agpl = scan.score(repo, "AI", 45)[0]
    assert mit > agpl


def test_score_is_bounded():
    repo = {
        "stargazers_count": 10_000_000,
        "forks_count": 1_000_000,
        "open_issues_count": 0,
        "pushed_at": "x",
        "name": "x",
        "description": "x",
    }
    assert 0 <= scan.score(repo, "AI", 100)[0] <= 100


def test_lscore_alias_available():
    assert scan.lscore("MIT") > scan.lscore("AGPL-3.0")