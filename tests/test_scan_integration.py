"""End-to-end scanner test using a stubbed GitHub client and a temp DB."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import scan as scan_mod
from scripts.persistence import connect, DEFAULT_DB
from tests.fixtures.github_responses import SEARCH_RESPONSE


@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    db = tmp_path / "radar.sqlite3"
    return db


def test_run_writes_rows_reports_and_events(tmp_db, monkeypatch):
    client = scan_mod.GitHubClient(token=None, retries=1, backoff=1.0)

    def fake_get_json(self, path, params=None):  # noqa: ARG001
        if path == "/search/repositories":
            return SEARCH_RESPONSE
        raise RuntimeError("unexpected path: " + path)

    with patch.object(scan_mod.GitHubClient, "get_json", new=fake_get_json):
        rows = scan_mod.run(db_path=tmp_db, fetch_releases=False, client=client)

    assert rows == 2

    conn = connect(tmp_db)
    repo_count = conn.execute("SELECT COUNT(*) FROM repositories").fetchone()[0]
    snap_count = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
    opp_count = conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    evt_types = [r[0] for r in conn.execute("SELECT event_type FROM events").fetchall()]
    conn.close()

    assert repo_count == 2
    assert snap_count == 2
    assert opp_count == 2
    # first scan -> all NEW_PROJECT events
    assert "NEW_PROJECT" in evt_types

    # reports were written under repo-root; ensure latest.json exists at root
    latest_json = (Path(scan_mod.ROOT) / "data" / "latest.json")
    assert latest_json.exists()
    payload = json.loads(latest_json.read_text(encoding="utf-8"))
    assert payload["count"] == 2
    assert {item["full_name"] for item in payload["top"]} == {
        "acme/awesome-ai",
        "acme/legacy-cms",
    }


def test_second_run_records_growth_and_events(tmp_db):
    client = scan_mod.GitHubClient(token=None, retries=1, backoff=1.0)

    def first(self, path, params=None):  # noqa: ARG001
        return SEARCH_RESPONSE

    with patch.object(scan_mod.GitHubClient, "get_json", new=first):
        scan_mod.run(db_path=tmp_db, fetch_releases=False, client=client)

    # Second scan: boost stars of the first repo to trigger rising/community events
    boosted = json.loads(json.dumps(SEARCH_RESPONSE))
    boosted["items"][0]["stargazers_count"] = 1500  # +25%
    boosted["items"][0]["forks_count"] = 250  # +66% vs 150 in fixture

    def second(self, path, params=None):  # noqa: ARG001
        return boosted

    with patch.object(scan_mod.GitHubClient, "get_json", new=second):
        scan_mod.run(db_path=tmp_db, fetch_releases=False, client=client)

    conn = connect(tmp_db)
    types = [r[0] for r in conn.execute("SELECT event_type FROM events ORDER BY id").fetchall()]
    conn.close()
    assert "RISING_PROJECT" in types
    assert "COMMUNITY_GROWTH" in types