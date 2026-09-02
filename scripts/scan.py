#!/usr/bin/env python3
"""Open Source Opportunity Radar scanner.

This module is the CLI entry point. Domain logic lives in:
  * scripts.github_client  — HTTP client with retries
  * scripts.persistence    — SQLite schema and CRUD
  * scripts.scoring        — deterministic scoring
  * scripts.events         — change detection
  * scripts.reports        — Markdown/JSON rendering
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.github_client import GitHubClient  # noqa: E402
from scripts.persistence import (  # noqa: E402
    DEFAULT_DB,
    init_db,
    connect,
    upsert_repository,
    previous_snapshot,
    insert_snapshot,
    upsert_opportunity,
    insert_event,
    record_run,
    utcnow,
)
from scripts.scoring import score, score_dict, lscore, license_score, analyze  # noqa: E402,F401
from scripts.events import detect  # noqa: E402
from scripts.reports import write_markdown, write_latest_json  # noqa: E402

__all__ = ["score", "analyze", "lscore", "license_score", "score_dict"]


def load_config(path: Path = ROOT / "config" / "discovery.yml") -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def discover(client: GitHubClient, cfg: dict) -> tuple[dict, int]:
    """Run all discovery queries; return (id -> (repo, category), errors)."""
    found: dict[int, tuple[dict, str]] = {}
    errors = 0
    limits = cfg.get("limits", {})
    per_query = limits.get("per_query", 20)
    min_stars = limits.get("min_stars", 100)
    sleep_between = limits.get("sleep_between", 0.15)
    for q in cfg.get("queries", []):
        try:
            params = {
                "q": f"{q['query']} stars:>={min_stars}",
                "sort": "stars",
                "order": "desc",
                "per_page": per_query,
            }
            data = client.get_json("/search/repositories", params)
            for r in data.get("items", []):
                found[r["id"]] = (r, q["category"])
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"discovery error [{q.get('name')}]: {exc}")
        if sleep_between:
            time.sleep(sleep_between)
    return found, errors


def fetch_release_tag(client: GitHubClient, repo: dict) -> str | None:
    if repo.get("_local_release_tag"):
        return repo["_local_release_tag"]
    full_name = repo.get("full_name")
    if not full_name:
        return None
    try:
        data = client.get_json(f"/repos/{full_name}/releases/latest")
        return data.get("tag_name")
    except Exception:  # noqa: BLE001
        return None


def compute_growth(previous: dict | None, current_stars: int) -> float:
    if previous is None:
        return 50.0
    prev = previous.get("stars") or 0
    if prev <= 0:
        return 50.0
    return max(0.0, min(100.0, 50.0 + (current_stars - prev) * 100.0 / max(prev, 1)))


def run(db_path: Path = DEFAULT_DB, fetch_releases: bool = False, client: GitHubClient | None = None) -> int:
    """Execute a full scan; returns the number of rows written."""
    started = utcnow()
    cfg = load_config()
    init_db(db_path)
    conn = connect(db_path)
    cur = conn.cursor()

    client = client or GitHubClient()
    found, errors = discover(client, cfg)

    max_repos = cfg.get("limits", {}).get("max_repositories", 250)
    now = utcnow()
    rows: list[tuple] = []

    for repo, category in list(found.values())[:max_repos]:
        prev = previous_snapshot(conn, repo["id"])
        discovered_at = upsert_repository(conn, repo, category, now)
        growth = compute_growth(prev, repo.get("stargazers_count", 0))
        release_tag = fetch_release_tag(client, repo) if fetch_releases else None
        insert_snapshot(conn, repo["id"], repo, now, release_tag)
        result = score_dict(repo, category, growth)
        upsert_opportunity(conn, repo["id"], now, result)
        for event_type, payload in detect(repo, prev, release_tag):
            insert_event(conn, repo["id"], now, event_type, payload)
        lic = (repo.get("license") or {}).get("spdx_id")
        rows.append(
            (result["score"], repo, growth, lic, result["best_path"], result["fastest_path"], result["long_term_path"], category)
        )

    rows.sort(reverse=True, key=lambda x: x[0])
    write_markdown(rows, generated_at=now)
    write_latest_json(rows, generated_at=now)
    finished = utcnow()
    record_run(conn, started, finished, len(rows), errors)
    conn.commit()
    conn.close()
    print(f"scan complete: {len(rows)} repositories, {errors} errors")
    return len(rows)


def main() -> None:
    run()


if __name__ == "__main__":
    main()