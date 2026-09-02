"""Unit tests for the scoring module."""
from scripts.scoring import score, score_dict, license_score, analyze, config


def _repo(license_id="MIT", stars=1000, forks=50, name="agent", description="AI agent"):
    return {
        "stargazers_count": stars,
        "forks_count": forks,
        "open_issues_count": 1,
        "pushed_at": "2026-09-01T00:00:00Z",
        "name": name,
        "description": description,
        "license": {"spdx_id": license_id} if license_id else None,
    }


def test_license_scores_are_ordered():
    mit = score(_repo("MIT"), "AI", 100)[0]
    agpl = score(_repo("AGPL-3.0"), "AI", 45)[0]
    assert mit > agpl


def test_score_is_bounded():
    s = score(_repo(stars=10_000_000, forks=1_000_000), "AI", 100)[0]
    assert 0 <= s <= 100


def test_unknown_license_has_lower_score_than_mit():
    assert license_score(None) < license_score("MIT")


def test_paths_for_ai_category():
    best, fast, long_term = score(_repo(), "AI", 60)[8:11]
    assert best == "AI SaaS"
    assert "Customization" in fast or "Integration" in fast
    assert long_term == "AI Platform"


def test_score_dict_has_all_keys():
    result = score_dict(_repo(), "Business", 55)
    for key in (
        "score", "growth", "license", "market", "saas", "ai",
        "localization", "time_to_money", "best_path", "fastest_path", "long_term_path",
    ):
        assert key in result


def test_growth_zero_when_no_previous():
    assert score(_repo(stars=500), "Documents", 0)[1] == 0.0


def test_analyze_alias_matches_score():
    repo = _repo()
    assert analyze(repo, "Finance", 60) == score(repo, "Finance", 60)


def test_weights_load_from_yaml():
    cfg = config()
    assert abs(sum(cfg.weights.values()) - 1.0) < 1e-6