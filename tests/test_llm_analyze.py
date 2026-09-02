"""Tests for llm_analyze: fallback quality, source tagging, persistence."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import llm_analyze


@pytest.fixture
def tmp_out(tmp_path: Path, monkeypatch) -> Path:
    out = tmp_path / "business-cases"
    out.mkdir()
    latest = tmp_path / "latest.json"
    latest.write_text(
        json.dumps(
            {
                "generated_at": "2026-09-02T00:00:00Z",
                "count": 2,
                "top": [
                    {
                        "full_name": "aimeos/aimeos-laravel",
                        "description": "Laravel ecommerce",
                        "language": "PHP",
                        "topics": ["ecommerce", "laravel"],
                        "license": "MIT",
                        "category": "E-commerce",
                        "score": 81.2,
                        "stars": 8694,
                    },
                    {
                        "full_name": "dangerous/agpl-tool",
                        "description": "strict license",
                        "language": "Python",
                        "topics": [],
                        "license": "AGPL-3.0",
                        "category": "AI",
                        "score": 70.0,
                        "stars": 100,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(llm_analyze, "OUT", out)
    monkeypatch.setattr(llm_analyze, "LATEST", latest)
    monkeypatch.setattr(llm_analyze, "TOP_N", 2)
    monkeypatch.setattr(llm_analyze, "FORCE", False)
    monkeypatch.setattr(llm_analyze, "KEY", "")
    return out


def test_fallback_is_repository_specific(tmp_out):
    aimeos = {"full_name": "aimeos/aimeos-laravel", "category": "E-commerce", "description": "Laravel ecommerce", "license": "MIT"}
    other = {"full_name": "dangerous/agpl-tool", "category": "AI", "description": "strict license", "license": "AGPL-3.0"}
    fa = llm_analyze.fallback(aimeos)
    fb = llm_analyze.fallback(other)
    assert "aimeos-laravel" in fa["what_it_does"]
    assert "agpl-tool" in fb["what_it_does"]
    assert fa["best_products"][0]["license_risk"] != fb["best_products"][0]["license_risk"]
    assert "AGPL" in fb["license_notes"]
    assert fa["license_notes"] != fb["license_notes"]


def test_main_uses_fallback_when_no_key(tmp_out):
    rc = llm_analyze.main()
    assert rc == 0
    files = sorted(tmp_out.iterdir())
    assert len(files) == 2
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["_source"] in {"fallback", "external"}


def test_existing_analysis_is_preserved_without_force(tmp_out):
    name = "aimeos/aimeos-laravel"
    path = tmp_out / (name.replace("/", "__") + ".json")
    path.write_text(
        json.dumps(
            {
                "what_it_does": "CUSTOM",
                "best_products": [{"product": "X", "customer": "Y", "monetization": "Z",
                                  "example_usage": "E", "sales_pitch": "S",
                                  "pricing": "P", "localization": "L",
                                  "difficulty": "کم", "time_to_money": "۱ هفته",
                                  "license_risk": "R"}],
                "_source": "freebuff",
            }
        ),
        encoding="utf-8",
    )
    rc = llm_analyze.main()
    assert rc == 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["what_it_does"] == "CUSTOM"
    assert payload["_source"] == "freebuff"


def test_force_overwrites_existing(tmp_out, monkeypatch):
    name = "aimeos/aimeos-laravel"
    path = tmp_out / (name.replace("/", "__") + ".json")
    path.write_text(json.dumps({"what_it_does": "OLD"}, ensure_ascii=False))
    monkeypatch.setattr(llm_analyze, "FORCE", True)
    rc = llm_analyze.main()
    assert rc == 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["what_it_does"] != "OLD"
    assert payload["_source"] == "fallback"