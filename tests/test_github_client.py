"""Tests for the GitHub HTTP client: retry/backoff and error handling."""
from unittest.mock import patch

import pytest

from scripts.github_client import GitHubClient
from urllib.error import HTTPError


class FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload


@pytest.fixture
def client():
    return GitHubClient(retries=3, backoff=1.0, sleep_between=0)


def test_returns_parsed_json(client):
    fake = FakeResponse(b'{"ok": true}')
    with patch("scripts.github_client.urlopen", return_value=fake):
        data = client.get_json("/repos/foo/bar")
    assert data == {"ok": True}


def test_retries_on_503_then_succeeds(client):
    err = HTTPError("https://api.github.com/x", 503, "boom", {}, None)
    fake = FakeResponse(b'{"ok": true}')
    with patch("scripts.github_client.urlopen", side_effect=[err, fake]) as mocked:
        data = client.get_json("/x")
    assert data == {"ok": True}
    assert mocked.call_count == 2


def test_non_retryable_status_raises_immediately(client):
    err = HTTPError("https://api.github.com/x", 404, "missing", {}, None)
    with patch("scripts.github_client.urlopen", side_effect=err) as mocked:
        with pytest.raises(HTTPError):
            client.get_json("/x")
    assert mocked.call_count == 1