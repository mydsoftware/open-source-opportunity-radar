"""Scoring module: deterministic metrics from GitHub metadata + YAML weights.

`score(repo, category, growth)` keeps the original signature so existing tests
and downstream callers continue to work.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "scoring.yml"

DEFAULT_WEIGHTS = {
    "popularity": 0.10,
    "growth": 0.15,
    "activity": 0.10,
    "community": 0.05,
    "technical_quality": 0.10,
    "commercial_freedom": 0.15,
    "market_potential": 0.10,
    "saas_potential": 0.10,
    "ai_opportunity": 0.05,
    "localization_opportunity": 0.05,
    "time_to_money": 0.05,
}

DEFAULT_LICENSE_SCORES = {
    "MIT": 100,
    "Apache-2.0": 95,
    "BSD-2-Clause": 95,
    "BSD-3-Clause": 95,
    "ISC": 95,
    "MPL-2.0": 75,
    "LGPL-3.0": 65,
    "LGPL-2.1": 65,
    "GPL-3.0": 55,
    "GPL-2.0": 55,
    "AGPL-3.0": 45,
    "SSPL-1.0": 20,
    "BSL-1.1": 25,
    None: 10,
}

DEFAULT_CATEGORY_SCORES = {
    "AI": 95,
    "Automation": 92,
    "E-commerce": 90,
    "Business": 90,
    "Documents": 89,
    "Low-code": 90,
    "IoT": 88,
    "Analytics": 87,
    "Developer": 86,
    "Games": 84,
    "Finance": 84,
    "Web": 82,
}


class ScoringConfig:
    def __init__(self, path: Path = CONFIG_PATH) -> None:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.weights = {**DEFAULT_WEIGHTS, **(raw.get("weights") or {})}
        license_cfg = raw.get("license_scores") or {}
        self.license_scores = {**DEFAULT_LICENSE_SCORES, **{k: v for k, v in license_cfg.items()}}
        category_cfg = raw.get("category_business_scores") or {}
        self.category_scores = {**DEFAULT_CATEGORY_SCORES, **{k: v for k, v in category_cfg.items()}}

    @property
    def weight_sum(self) -> float:
        return sum(self.weights.values())


_CONFIG: ScoringConfig | None = None


def config() -> ScoringConfig:
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = ScoringConfig()
    return _CONFIG


def reset_config_cache() -> None:
    global _CONFIG
    _CONFIG = None


def license_score(spdx_id: str | None, cfg: ScoringConfig | None = None) -> float:
    cfg = cfg or config()
    return cfg.license_scores.get(spdx_id, 40)


def lscore(spdx_id: str | None) -> float:
    """Backward-compatible alias matching the original scan.lscore signature."""
    return license_score(spdx_id)


def _popularity(repo: dict[str, Any]) -> float:
    stars = repo.get("stargazers_count", 0)
    return min(100.0, 20.0 + (max(stars, 0)) ** 0.5 * 2.2)


def _community(repo: dict[str, Any]) -> float:
    forks = repo.get("forks_count", 0)
    return min(100.0, 20.0 + (max(forks, 0)) ** 0.5 * 2.5)


def _activity(repo: dict[str, Any]) -> float:
    return 90.0 if repo.get("pushed_at") else 20.0


def _technical_quality(repo: dict[str, Any]) -> float:
    score = 75.0
    if repo.get("description"):
        score += 5
    if repo.get("license"):
        score += 5
    if repo.get("default_branch"):
        score += 2
    if repo.get("archived"):
        score -= 25
    return max(0.0, min(100.0, score))


def _market(category: str, cfg: ScoringConfig | None = None) -> float:
    cfg = cfg or config()
    return float(cfg.category_scores.get(category, 75))


def _ai(category: str, repo: dict[str, Any]) -> float:
    if category == "AI":
        return 95.0
    text = (repo.get("name", "") + " " + (repo.get("description") or "")).lower()
    if any(token in text for token in ("ai", "llm", "agent", "rag")):
        return 80.0
    return 45.0


def _saas(category: str, market: float) -> float:
    if category in {"AI", "Automation", "Business", "E-commerce", "Documents", "Analytics", "Low-code"}:
        return min(98.0, market + 8)
    return min(98.0, market)


def _localization(category: str) -> float:
    if category in {"Business", "E-commerce", "Documents", "Finance", "Analytics", "Education"}:
        return 88.0
    return 62.0


def _time_to_money(category: str, growth: float) -> float:
    fast_categories = {"AI", "Business", "E-commerce", "Documents", "Automation"}
    base = 80.0 if category in fast_categories else 55.0
    boost = min(20.0, max(0.0, growth - 50.0) * 0.4)
    return min(100.0, base + boost)


def _paths(category: str) -> tuple[str, str, str]:
    if category == "AI":
        return ("AI SaaS", "Integration + Customization", "AI Platform")
    if category in {"Business", "E-commerce", "Documents", "Analytics", "Low-code"}:
        return ("Vertical SaaS", "Installation + Customization", "Enterprise SaaS")
    if category in {"IoT", "Developer"}:
        return ("Managed Service", "Setup + Support", "Enterprise Platform")
    return ("SaaS / Services", "Installation + Customization", "Platform / Enterprise")


def score(
    repo: dict[str, Any],
    category: str,
    growth: float,
    cfg: ScoringConfig | None = None,
) -> tuple[float, float, float, float, float, float, float, float, str, str, str]:
    """Return (total, growth, license, market, saas, ai, localization, time_to_money, best, fastest, long_term)."""
    cfg = cfg or config()
    metrics = {
        "popularity": _popularity(repo),
        "growth": float(growth),
        "activity": _activity(repo),
        "community": _community(repo),
        "technical_quality": _technical_quality(repo),
        "commercial_freedom": license_score((repo.get("license") or {}).get("spdx_id"), cfg),
        "market_potential": _market(category, cfg),
        "saas_potential": _saas(category, _market(category, cfg)),
        "ai_opportunity": _ai(category, repo),
        "localization_opportunity": _localization(category),
        "time_to_money": _time_to_money(category, float(growth)),
    }
    weight_sum = max(cfg.weight_sum, 1e-9)
    total = sum(metrics[k] * cfg.weights.get(k, 0.0) for k in metrics) / weight_sum * 1.0
    best, fast, long_term = _paths(category)
    return (
        round(total, 1),
        round(float(growth), 1),
        round(metrics["commercial_freedom"], 1),
        round(metrics["market_potential"], 1),
        round(metrics["saas_potential"], 1),
        round(metrics["ai_opportunity"], 1),
        round(metrics["localization_opportunity"], 1),
        round(metrics["time_to_money"], 1),
        best,
        fast,
        long_term,
    )


def analyze(repo: dict[str, Any], category: str, growth: float) -> tuple:
    """Backward-compatible alias."""
    return score(repo, category, growth)


def score_dict(repo: dict[str, Any], category: str, growth: float, cfg: ScoringConfig | None = None) -> dict:
    """Return a flat dictionary suitable for persistence / API output."""
    s = score(repo, category, growth, cfg)
    return {
        "score": s[0],
        "growth": s[1],
        "license": s[2],
        "market": s[3],
        "saas": s[4],
        "ai": s[5],
        "localization": s[6],
        "time_to_money": s[7],
        "best_path": s[8],
        "fastest_path": s[9],
        "long_term_path": s[10],
    }