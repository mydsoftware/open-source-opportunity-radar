"""Verify that init_db migrates legacy schemas without losing data."""
import sqlite3
from pathlib import Path

from scripts.persistence import init_db, connect


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / "legacy.sqlite3"
    # create a legacy database matching the pre-refactor schema
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE repositories (
                id INTEGER PRIMARY KEY, full_name TEXT UNIQUE, name TEXT, url TEXT,
                description TEXT, language TEXT, license TEXT, topics TEXT,
                category TEXT, discovered_at TEXT, updated_at TEXT
            );
            CREATE TABLE snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT, repo_id INTEGER, scanned_at TEXT,
                stars INTEGER, forks INTEGER, watchers INTEGER, open_issues INTEGER,
                pushed_at TEXT, updated_at TEXT
            );
            CREATE TABLE opportunities (
                repo_id INTEGER PRIMARY KEY, scanned_at TEXT, score REAL,
                growth_score REAL, license_score REAL, market_score REAL,
                saas_score REAL, ai_score REAL, localization_score REAL,
                best_path TEXT, fastest_path TEXT, long_term_path TEXT, rationale TEXT
            );
            CREATE TABLE scan_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT, finished_at TEXT,
                repos_found INTEGER, errors INTEGER
            );
            INSERT INTO repositories(id, full_name, name) VALUES (1, 'acme/test', 'test');
            """
        )
        conn.commit()

    init_db(db)

    conn = connect(db)
    cols_repo = {r[1] for r in conn.execute("PRAGMA table_info(repositories)").fetchall()}
    cols_snap = {r[1] for r in conn.execute("PRAGMA table_info(snapshots)").fetchall()}
    cols_opp = {r[1] for r in conn.execute("PRAGMA table_info(opportunities)").fetchall()}
    rows = conn.execute("SELECT full_name FROM repositories").fetchall()
    conn.close()

    assert "default_branch" in cols_repo
    assert "archived" in cols_repo
    assert "created_at" in cols_repo
    assert "release_tag" in cols_snap
    assert "time_to_money_score" in cols_opp
    # legacy data preserved
    assert rows == [("acme/test",)]


def test_init_db_safe_to_rerun(tmp_path: Path) -> None:
    db = tmp_path / "fresh.sqlite3"
    init_db(db)
    init_db(db)  # second run must not raise
    assert db.exists()