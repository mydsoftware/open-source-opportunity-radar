"""SQLite persistence for repositories, snapshots, opportunities, and events."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_ROOT = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DB = DB_ROOT / "radar.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS repositories (
    id INTEGER PRIMARY KEY,
    full_name TEXT UNIQUE,
    name TEXT,
    url TEXT,
    description TEXT,
    language TEXT,
    license TEXT,
    topics TEXT,
    category TEXT,
    default_branch TEXT,
    archived INTEGER DEFAULT 0,
    created_at TEXT,
    discovered_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER,
    scanned_at TEXT,
    stars INTEGER,
    forks INTEGER,
    watchers INTEGER,
    open_issues INTEGER,
    pushed_at TEXT,
    updated_at TEXT,
    release_tag TEXT
);

CREATE TABLE IF NOT EXISTS opportunities (
    repo_id INTEGER PRIMARY KEY,
    scanned_at TEXT,
    score REAL,
    growth_score REAL,
    license_score REAL,
    market_score REAL,
    saas_score REAL,
    ai_score REAL,
    localization_score REAL,
    time_to_money_score REAL,
    best_path TEXT,
    fastest_path TEXT,
    long_term_path TEXT,
    rationale TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER,
    scanned_at TEXT,
    event_type TEXT,
    payload TEXT
);

CREATE TABLE IF NOT EXISTS scan_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    finished_at TEXT,
    repos_found INTEGER,
    errors INTEGER
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db(db_path: Path = DEFAULT_DB) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def connect(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def upsert_repository(conn: sqlite3.Connection, repo: dict[str, Any], category: str, discovered_at: str) -> str:
    """Insert or update a repository row. Returns discovered_at (preserved if exists)."""
    lic = (repo.get("license") or {}).get("spdx_id")
    archived = 1 if repo.get("archived") else 0
    existing = conn.execute(
        "SELECT discovered_at FROM repositories WHERE id=?", (repo["id"],)
    ).fetchone()
    discovered = existing[0] if existing and existing[0] else discovered_at
    conn.execute(
        """INSERT OR REPLACE INTO repositories
           (id, full_name, name, url, description, language, license, topics, category,
            default_branch, archived, created_at, discovered_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            repo["id"],
            repo["full_name"],
            repo["name"],
            repo["html_url"],
            repo.get("description"),
            repo.get("language"),
            lic,
            json.dumps(repo.get("topics", []), ensure_ascii=False),
            category,
            repo.get("default_branch"),
            archived,
            repo.get("created_at"),
            discovered,
            utcnow(),
        ),
    )
    return discovered


def previous_snapshot(conn: sqlite3.Connection, repo_id: int) -> dict | None:
    row = conn.execute(
        "SELECT stars, forks, scanned_at, release_tag FROM snapshots WHERE repo_id=? ORDER BY id DESC LIMIT 1",
        (repo_id,),
    ).fetchone()
    if not row:
        return None
    return {"stars": row[0], "forks": row[1], "scanned_at": row[2], "release_tag": row[3]}


def insert_snapshot(conn: sqlite3.Connection, repo_id: int, repo: dict, scanned_at: str, release_tag: str | None) -> None:
    conn.execute(
        """INSERT INTO snapshots(repo_id, scanned_at, stars, forks, watchers, open_issues, pushed_at, updated_at, release_tag)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (
            repo_id,
            scanned_at,
            repo.get("stargazers_count", 0),
            repo.get("forks_count", 0),
            repo.get("watchers_count", 0),
            repo.get("open_issues_count", 0),
            repo.get("pushed_at"),
            repo.get("updated_at"),
            release_tag,
        ),
    )


def upsert_opportunity(conn: sqlite3.Connection, repo_id: int, scanned_at: str, result: dict) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO opportunities
           (repo_id, scanned_at, score, growth_score, license_score, market_score,
            saas_score, ai_score, localization_score, time_to_money_score,
            best_path, fastest_path, long_term_path, rationale)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            repo_id,
            scanned_at,
            result["score"],
            result["growth"],
            result["license"],
            result["market"],
            result["saas"],
            result["ai"],
            result["localization"],
            result["time_to_money"],
            result["best_path"],
            result["fastest_path"],
            result["long_term_path"],
            "Metadata-based opportunity hypothesis; not a revenue guarantee.",
        ),
    )


def insert_event(conn: sqlite3.Connection, repo_id: int, scanned_at: str, event_type: str, payload: dict) -> None:
    conn.execute(
        "INSERT INTO events(repo_id, scanned_at, event_type, payload) VALUES (?,?,?,?)",
        (repo_id, scanned_at, event_type, json.dumps(payload, ensure_ascii=False)),
    )


def record_run(conn: sqlite3.Connection, started_at: str, finished_at: str, repos_found: int, errors: int) -> None:
    conn.execute(
        "INSERT INTO scan_runs(started_at, finished_at, repos_found, errors) VALUES (?,?,?,?)",
        (started_at, finished_at, repos_found, errors),
    )
    conn.commit()