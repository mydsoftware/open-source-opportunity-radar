"""GitHub API client with retries, session reuse, and rate-limit awareness."""
from __future__ import annotations

import json
import os
import time
from typing import Any, Iterable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://api.github.com"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 1.6

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class GitHubClient:
    """Thin urllib-based client with exponential backoff and shared headers."""

    def __init__(
        self,
        token: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        backoff: float = DEFAULT_BACKOFF,
        sleep_between: float = 0.0,
    ) -> None:
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff = backoff
        self.sleep_between = sleep_between
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "open-source-opportunity-radar/1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def get_json(self, path: str, params: Mapping[str, Any] | None = None) -> dict:
        url = API + path
        if params:
            url += ("&" if "?" in url else "?") + urlencode(params)
        attempt = 0
        delay = 1.0
        last_error: Exception | None = None
        while attempt < self.retries:
            attempt += 1
            req = Request(url, headers=self.headers)
            try:
                with urlopen(req, timeout=self.timeout) as resp:
                    if self.sleep_between:
                        time.sleep(self.sleep_between)
                    return json.loads(resp.read().decode("utf-8"))
            except HTTPError as exc:
                last_error = exc
                if exc.code in RETRYABLE_STATUS and attempt < self.retries:
                    time.sleep(delay)
                    delay *= self.backoff
                    continue
                raise
            except URLError as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(delay)
                    delay *= self.backoff
                    continue
                raise
        raise RuntimeError(f"github request failed after {self.retries} attempts: {last_error}")

    def paginate(self, path: str, params: Mapping[str, Any] | None = None, per_page: int = 100) -> Iterable[dict]:
        page = 1
        while True:
            merged = {"per_page": per_page, "page": page, **(params or {})}
            items = self.get_json(path, merged)
            if not items:
                return
            for item in items:
                yield item
            if len(items) < per_page:
                return
            page += 1