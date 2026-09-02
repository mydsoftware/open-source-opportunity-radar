"""Tests for event detection."""
from scripts.events import (
    NEW_PROJECT,
    RISING_PROJECT,
    COMMUNITY_GROWTH,
    ACTIVITY_SURGE,
    MAJOR_RELEASE,
    detect,
)


def _repo(stars=100, forks=10, pushed_at="2026-08-30T00:00:00Z", repo_id=42):
    return {
        "id": repo_id,
        "stargazers_count": stars,
        "forks_count": forks,
        "pushed_at": pushed_at,
    }


def test_first_seen_marks_new_project():
    events = detect(_repo(), previous=None, current_release=None)
    assert (NEW_PROJECT, {"repo_id": 42, "stars": 100}) in events


def test_rising_when_stars_grow_above_threshold():
    events = detect(_repo(stars=120), previous={"stars": 100}, current_release=None)
    types = [t for t, _ in events]
    assert RISING_PROJECT in types


def test_community_growth_event():
    events = detect(_repo(forks=20), previous={"stars": 100, "forks": 10}, current_release=None)
    types = [t for t, _ in events]
    assert COMMUNITY_GROWTH in types


def test_activity_surge_for_recent_push():
    events = detect(_repo(), previous={"stars": 100}, current_release=None)
    types = [t for t, _ in events]
    assert ACTIVITY_SURGE in types


def test_release_change_detected():
    events = detect(_repo(), previous={"stars": 100, "release_tag": "v1.0"}, current_release="v2.0")
    types = [t for t, _ in events]
    assert MAJOR_RELEASE in types