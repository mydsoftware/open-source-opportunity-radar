"""Detect repository events by comparing a fresh snapshot to the previous one."""
from __future__ import annotations

from typing import Any

NEW_PROJECT = "NEW_PROJECT"
RISING_PROJECT = "RISING_PROJECT"
MAJOR_RELEASE = "MAJOR_RELEASE"
LICENSE_CHANGE = "LICENSE_CHANGE"
COMMUNITY_GROWTH = "COMMUNITY_GROWTH"
ACTIVITY_SURGE = "ACTIVITY_SURGE"
COMMERCIAL_SIGNAL = "COMMERCIAL_SIGNAL"

STAR_DELTA_RISING = 0.10
COMMUNITY_DELTA = 0.15
ACTIVITY_DAYS = 30


def _star_delta_pct(prev_stars: int, current_stars: int) -> float:
    if prev_stars <= 0:
        return 0.0
    return (current_stars - prev_stars) / prev_stars


def detect(repo: dict[str, Any], previous: dict | None, current_release: str | None) -> list[tuple[str, dict]]:
    """Return a list of (event_type, payload) tuples for the given repo."""
    events: list[tuple[str, dict]] = []
    repo_id = repo["id"]
    current_stars = repo.get("stargazers_count", 0)
    current_forks = repo.get("forks_count", 0)

    if previous is None:
        events.append((NEW_PROJECT, {"repo_id": repo_id, "stars": current_stars}))
        return events

    prev_stars = previous.get("stars") or 0
    prev_forks = previous.get("forks") or 0
    prev_release = previous.get("release_tag")

    star_pct = _star_delta_pct(prev_stars, current_stars)
    if star_pct >= STAR_DELTA_RISING:
        events.append(
            (
                RISING_PROJECT,
                {"repo_id": repo_id, "delta_stars": current_stars - prev_stars, "delta_pct": round(star_pct, 3)},
            )
        )

    if prev_forks > 0 and (current_forks - prev_forks) / prev_forks >= COMMUNITY_DELTA:
        events.append(
            (
                COMMUNITY_GROWTH,
                {"repo_id": repo_id, "delta_forks": current_forks - prev_forks},
            )
        )

    pushed_at = repo.get("pushed_at")
    if pushed_at and len(pushed_at) >= 10:
        try:
            from datetime import datetime, timezone
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - pushed).days
            if age_days <= ACTIVITY_DAYS:
                events.append((ACTIVITY_SURGE, {"repo_id": repo_id, "age_days": age_days}))
        except ValueError:
            pass

    if current_release and current_release != prev_release:
        events.append(
            (
                MAJOR_RELEASE,
                {"repo_id": repo_id, "from": prev_release, "to": current_release},
            )
        )

    return events