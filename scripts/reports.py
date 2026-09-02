"""Render Markdown and JSON artifacts for the latest scan run."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORTS = ROOT / "reports"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_markdown(rows: Iterable[tuple], generated_at: str | None = None, top_n: int = 100) -> Path:
    """rows: iterable of (score, repo, growth, license, best, fastest, long_term, category)."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    generated_at = generated_at or _now_iso()
    rows = list(rows)
    lines = ["# Open Source Opportunity Radar", "", f"Generated: {generated_at}", f"Repositories scanned: {len(rows)}", "", "## Top Opportunities", ""]
    for i, (s, r, g, lic, best, fast, long_term, cat) in enumerate(rows[:top_n], 1):
        lines += [
            f"### {i}. [{r['full_name']}]({r['html_url']}) — {s}/100",
            f"- Description: {r.get('description') or 'N/A'}",
            f"- Category: {cat}",
            f"- Stars: {r['stargazers_count']:,} | Forks: {r['forks_count']:,} | Growth signal: {g:.1f}",
            f"- License: {lic or 'Unknown'}",
            f"- Best: **{best}** | **Fastest: {fast}** | **Long-term: {long_term}**",
            "",
        ]
    out = REPORTS / "latest.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_latest_json(rows: Iterable[tuple], generated_at: str | None = None, top_n: int = 100) -> Path:
    DATA.mkdir(parents=True, exist_ok=True)
    generated_at = generated_at or _now_iso()
    payload = {
        "generated_at": generated_at,
        "count": 0,
        "top": [],
    }
    rows = list(rows)
    payload["count"] = len(rows)
    payload["top"] = [
        {
            "full_name": r["full_name"],
            "url": r["html_url"],
            "score": s,
            "stars": r["stargazers_count"],
            "license": lic,
            "best_path": best,
            "description": r.get("description"),
            "category": cat,
            "language": r.get("language"),
            "topics": r.get("topics", []),
        }
        for s, r, g, lic, best, fast, long_term, cat in rows[:top_n]
    ]
    out = DATA / "latest.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out