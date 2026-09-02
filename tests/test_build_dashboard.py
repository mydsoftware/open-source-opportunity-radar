"""Tests for the dashboard analysis loader."""
import json
from pathlib import Path

import scripts.build_dashboard as bd


def _write_case(cases_dir: Path, full_name: str, payload: dict) -> None:
    (cases_dir / (full_name.replace("/", "__") + ".json")).write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def test_missing_case_returns_waiting(tmp_path: Path):
    cases = tmp_path / "cases"
    cases.mkdir()
    original = bd.CASES
    bd.CASES = cases
    try:
        item = {"full_name": "aimeos/aimeos-laravel"}
        result = bd.get_analysis(item)
        assert result["_missing"] is True
    finally:
        bd.CASES = original


def test_present_case_is_normalized(tmp_path: Path):
    cases = tmp_path / "cases"
    cases.mkdir()
    _write_case(
        cases,
        "aimeos/aimeos-laravel",
        {
            "what_it_does": "پکیج e-commerce برای Laravel",
            "problem_solved": "نصب سریع فروشگاه",
            "best_products": [
                {
                    "product": "سرویس استقرار",
                    "customer": "فروشگاه‌ها",
                    "monetization": "Setup",
                    "pricing": "۵۰ میلیون",
                    "example_usage": "نصب Laravel",
                    "sales_pitch": "پنل فارسی",
                    "localization": "جلالی",
                    "difficulty": "متوسط",
                    "time_to_money": "۱ هفته",
                    "license_risk": "MIT",
                },
                {
                    "product": "vertical SaaS",
                    "customer": "B2B",
                    "monetization": "اشتراک",
                    "pricing": "۲۰۰ میلیون",
                    "example_usage": "multi-vendor",
                    "sales_pitch": "vertical",
                    "localization": "ERP",
                    "difficulty": "زیاد",
                    "time_to_money": "۶ ماه",
                    "license_risk": "MIT",
                },
            ],
            "recommendation": "با استقرار شروع کنید",
            "confidence": 75,
            "license_notes": "MIT",
            "_source": "freebuff",
        },
    )
    original = bd.CASES
    bd.CASES = cases
    try:
        result = bd.get_analysis({"full_name": "aimeos/aimeos-laravel"})
        assert result.get("_missing") is not True
        assert "Laravel" in result["use"]
        assert "سرویس استقرار" in result["fast_product"]
        assert "vertical SaaS" in result["long_product"]
        assert result["source"] == "freebuff"
    finally:
        bd.CASES = original


def test_fallback_when_business_opportunities_used(tmp_path: Path):
    cases = tmp_path / "cases"
    cases.mkdir()
    _write_case(
        cases,
        "x/y",
        {
            "what_it_does": "شرح",
            "problem_solved": "مسئله",
            "business_opportunities": [
                {"product": "P", "customer": "C", "monetization": "M"}
            ],
            "_source": "llm",
        },
    )
    original = bd.CASES
    bd.CASES = cases
    try:
        result = bd.get_analysis({"full_name": "x/y"})
        assert result["source"] == "llm"
        assert result["fast_product"] == "P"
    finally:
        bd.CASES = original