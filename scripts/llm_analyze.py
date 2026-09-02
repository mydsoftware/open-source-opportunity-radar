#!/usr/bin/env python3
"""Generate repository-specific business analyses in Persian.

For each repository in `data/latest.json`, call an OpenAI-compatible LLM
to produce a tailored analysis and persist it to
`data/business-cases/<owner>__<repo>.json`.

The system is robust:
  * If LLM_API_KEY is not set, every entry receives a richer deterministic
    fallback that references the project's actual fields (not a template).
  * If the LLM call fails or returns an invalid payload, the fallback is
    used instead and the failure is logged.
  * When `force=True`, existing files (e.g. those produced by an external
    Freebuff agent) are kept untouched.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

API = (
    os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    + "/chat/completions"
)
KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b:free")
TIMEOUT = int(os.getenv("LLM_TIMEOUT", "90"))
TOP_N = int(os.getenv("LLM_TOP_N", "100"))
FORCE = os.getenv("LLM_FORCE", "0") == "1"
OUT = ROOT / "data" / "business-cases"
LATEST = ROOT / "data" / "latest.json"

PROMPT = """تو تحلیلگر ارشد Open Source، Product و Business هستی.

وظیفه: برای یک Repository مشخص، تحلیل کاملاً اختصاصی و متمایز بنویس.
این تحلیل باید برای همان Repository یکتا باشد، نه متن تکراری برای پروژه‌های دیگر.

قوانین سخت:
- از نام، توضیح، زبان، Topics و License واقعی Repository استفاده کن.
- حداقل ۲ فرصت تجاری واقعی و متمایز پیشنهاد بده (نه «پنل فارسی بساز»).
- فرصت اول باید سریع‌ترین مسیر درآمد باشد.
- فرصت دوم یا سوم باید بلندمدت یا enterprise باشد.
- برای فرصت‌ها، مدل درآمد، سناریوی واقعی مشتری، و pitch فروش فارسی بده.
- اگر لایسنس محدودکننده است (AGPL/SSPL/BSL)، صریحاً بگو فروش مستقیم ممکن نیست و مدل Managed/Service پیشنهاد بده.
- هیچ درآمدی را تضمین نکن. confidence بین ۳۰ تا ۸۵.
- متن‌های طولانی‌تر (هر بخش حداقل ۲ جمله) بنویس تا عمق تحلیل مشخص باشد.
- خروجی فقط JSON معتبر. هیچ متن اضافی قبل یا بعد از JSON نباشد.

کلیدهای JSON خروجی (دقیقاً):
{
  "what_it_does": "...",             // 2-4 جمله درباره قابلیت واقعی پروژه
  "problem_solved": "...",            // چه دردی را حل می‌کند
  "why_it_matters": "...",            // چرا این فرصت تجاری مهم است
  "best_products": [                  // آرایه‌ای از محصولات پیشنهادی
    {
      "product": "...",               // نام/شرح محصول
      "customer": "...",              // مشتری هدف مشخص
      "monetization": "...",          // مدل درآمد
      "pricing": "...",               // قیمت‌گذاری پیشنهادی
      "example_usage": "...",         // سناریوی واقعی استفاده
      "sales_pitch": "...",           // متن فروش
      "localization": "...",          // فرصت بومی‌سازی مختص این محصول
      "difficulty": "کم|متوسط|زیاد",
      "time_to_money": "...",         // تخمین زمان
      "license_risk": "..."           // بررسی لایسنس
    }
  ],
  "recommendation": "...",             // توصیه نهایی برای اقدام
  "confidence": 60,                   // عدد 0-100
  "license_notes": "..."              // یادداشت درباره لایسنس
}
"""


def _category_insights(category: str) -> dict[str, str]:
    """Per-category hooks so the fallback is meaningfully different."""
    table = {
        "AI": {
            "fast_model": "سرویس API با استفاده از قابلیت‌های AI این پروژه + اشتراک ماهانه",
            "long_model": "پلتفرم SaaS هوش مصنوعی برای صنایع خاص",
            "weakness": "نیاز به API key از provider و هزینه inference",
        },
        "E-commerce": {
            "fast_model": "نصب + سفارشی‌سازی برای فروشگاه‌های متوسط",
            "long_model": "Vertical SaaS برای صنایع خاص (پزشکی، پوشاک، مواد غذایی)",
            "weakness": "نیاز به درگاه پرداخت و سیستم ارسال",
        },
        "Business": {
            "fast_model": "CRM/ERP به‌صورت Managed برای SME",
            "long_model": "Vertical SaaS با اتوماسیون فرایندهای کسب‌وکار",
            "weakness": "نیاز به integration با سیستم‌های موجود",
        },
        "Automation": {
            "fast_model": "اتوماسیون فرایندهای دستی تیم‌های کوچک",
            "long_model": "پلتفRPA  برای سازمان‌های متوسط",
            "weakness": "پیچیدگی تنظیم workflowها",
        },
        "Developer": {
            "fast_model": "سرویس ابری میزبان + پشتیبانی",
            "long_model": "پلتفرم enterprise با SLA و SLA-based pricing",
            "weakness": "رقابت شدید با محصولات تجاری موجود",
        },
        "Documents": {
            "fast_model": "سرویس پردازش اسناد فارسی",
            "long_model": "پلتفرم BPM با قابلیت OCR و استخراج داده",
            "weakness": "نیاز به dataset زبان فارسی",
        },
        "Finance": {
            "fast_model": "ابزار تحلیل برای معامله‌گران خرد",
            "long_model": "پلتفرم quantitative با API",
            "weakness": "مقررات سخت‌گیرانه مالی",
        },
        "Low-code": {
            "fast_model": "استقرار + آموزش برای تیم‌های غیرفنی",
            "long_model": "پلتفرم سازمانی با workflow پیچیده",
            "weakness": "نیاز به مستندسازی فارسی قوی",
        },
        "IoT": {
            "fast_model": "نصب + مانیتورینگ برای SME",
            "long_model": "پلتفرم enterprise با dashboard و alerting",
            "weakness": "نیاز به سخت‌افزار",
        },
        "Analytics": {
            "fast_model": "داشبود آماده برای کسب‌وکارها",
            "long_model": "پلتفرم BI با AI assistant",
            "weakness": "نیاز به data integration",
        },
        "Games": {
            "fast_model": "استودیو بازی‌سازی + engine training",
            "long_model": "پلتفرم توسعه بازی SaaS",
            "weakness": "بازار محدود",
        },
        "Web": {
            "fast_model": "استقرار سایت + محتوا",
            "long_model": "پلتفرم CMS-as-a-Service",
            "weakness": "رقابت زیاد",
        },
    }
    return table.get(category, {
        "fast_model": "سرویس استقرار + سفارشی‌سازی",
        "long_model": "پلتفرم SaaS تخصصی",
        "weakness": "نیاز به تحلیل بازار هدف",
    })


def fallback(item: dict) -> dict:
    """Deterministic fallback that uses actual fields of the repo."""
    name = item.get("full_name") or "این پروژه"
    description = item.get("description") or "توضیح کافی در GitHub ثبت نشده است."
    category = item.get("category") or "سایر"
    language = item.get("language") or "نامشخص"
    topics = item.get("topics") or []
    topics_text = "، ".join(topics[:6]) if topics else category
    license_name = item.get("license") or "نامشخص"
    short_name = name.split("/")[-1]
    insights = _category_insights(category)

    if license_name in {"AGPL-3.0", "SSPL-1.0", "BSL-1.1"}:
        monetization_fast = (
            "فروش مستقیم نرم‌افزار ممکن نیست؛ مدل درآمد = "
            "Managed Service + سفارشی‌سازی + پشتیبانی ممتاز + SLA."
        )
        licensing = (
            f"لایسنس {license_name} محدودکننده است. "
            "فروش مجدد یا ارائه به‌عنوان SaaS رقابتی نیاز به بررسی دقیق حقوقی دارد."
        )
    else:
        monetization_fast = (
            "هزینه راه‌اندازی یکبار + اشتراک ماهانه + بسته‌های سفارشی‌سازی + "
            "پشتیبانی سطح بالا با SLA."
        )
        licensing = (
            f"لایسنس {license_name} برای استفاده تجاری مشکلی ایجاد نمیکند، "
            "ولی NOTICE و وابستگی‌ها را قبل از فروش بررسی کنید."
        )

    fast_product = (
        f"«{short_name} به‌عنوان سرویس» بر پایه قابلیت واقعی «{name}»: "
        f"{insights['fast_model']}. "
        f"این محصول برای رفع خلأ {insights['weakness']} در بازار هدف طراحی می‌شود."
    )
    long_product = (
        f"«پلتفرم {category} تخصصی» بر پایه «{name}»: {insights['long_model']}. "
        "این محصول پس از اثبات تقاضا در مرحله اول، توسعه می‌یابد."
    )

    return {
        "what_it_does": (
            f"«{name}» یک پروژه {category} به زبان {language} است. "
            f"توضیح رسمی: {description} "
            f"موضوعات مرتبط در GitHub: {topics_text}."
        ),
        "problem_solved": (
            f"این پروژه مشکل {insights['weakness']} را هدف قرار میدهد. "
            f"کسب‌وکارهایی که با {topics_text} سروکار دارند، "
            "می‌توانند با استقرار این قابلیت، زمان و هزینه توسعه را کاهش دهند."
        ),
        "why_it_matters": (
            f"ترکیب {category} + {language} یک فرصت بازار است چون "
            f"پروژه‌های مشابه یا وجود ندارند یا فارسی‌سازی نشده‌اند. "
            "ورود زودهنگام به این حوزه مزیت رقابتی پایدار ایجاد می‌کند."
        ),
        "best_products": [
            {
                "product": fast_product,
                "customer": (
                    f"تیم‌های کوچک و متوسط در حوزه {category} که به دنبال "
                    "راه‌حل سریع بدون سرمایه‌گذاری سنگین اولیه هستند."
                ),
                "monetization": monetization_fast,
                "pricing": "Setup یکبار ۵۰–۲۰۰ میلیون تومان + اشتراک ماهانه ۱۰–۳۰ میلیون.",
                "example_usage": (
                    f"یک فروشگاه آنلاین {category} می‌تواند بدون تیم فنی داخلی، "
                    f"ظرف یک هفته از قابلیت «{short_name}» در فرایند روزانه خود استفاده کند."
                ),
                "sales_pitch": (
                    f"«ما قابلیت {short_name} را برای شما فارسی‌سازی، نصب و پشتیبانی می‌کنیم. "
                    "ظرف یک هفته اولین نتیجه را می‌بینید، بدون نیاز به تیم فنی اختصاصی.»"
                ),
                "localization": (
                    f"برای این محصول، بومی‌سازی حیاتی است: "
                    "رابط فارسی/RTL، تقویم جلالی، اتصال به درگاه‌های ایرانی، "
                    "و مستندات فارسی."
                ),
                "difficulty": "متوسط",
                "time_to_money": "۱ تا ۳ هفته برای اولین استقرار واقعی.",
                "license_risk": licensing,
            },
            {
                "product": long_product,
                "customer": (
                    f"سازمان‌های متوسط و بزرگ در صنایع مرتبط با {topics_text}."
                ),
                "monetization": "اشتراک سازمانی + توسعه سفارشی + integration fee.",
                "pricing": "۵۰–۲۰۰ میلیون ماهانه بسته به SLA و حجم.",
                "example_usage": (
                    f"یک شرکت بزرگ {category} می‌تواند «{short_name}» را با "
                    "تنظیمات سازمانی، SLA، و یکپارچگی ERP داخلی مستقر کند."
                ),
                "sales_pitch": (
                    f"«پلتفرم ما بر پایه {short_name}، جایگزین سیستم فعلی شما می‌شود "
                    "با هزینه کمتر و انعطاف بیشتر.»"
                ),
                "localization": (
                    "یکپارچگی با سیستم‌های سازمانی ایرانی، احراز هویت سازمانی، "
                    "گزارش‌دهی مطابق با مقررات."
                ),
                "difficulty": "زیاد",
                "time_to_money": "۲ تا ۶ ماه برای اولین قرارداد سازمانی.",
                "license_risk": licensing,
            },
        ],
        "recommendation": (
            f"پیشنهاد: ابتدا فرصت اول ({insights['fast_model']}) را برای "
            f"یک مشتری نمونه اجرا کنید، نتیجه مستند کنید، سپس فرصت دوم "
            f"({insights['long_model']}) را توسعه دهید. "
            "این مسیر هم ریسک را کم می‌کند و هم به شما زمان می‌دهد تا "
            "بازار را بهتر بشناسید."
        ),
        "confidence": 55,
        "license_notes": licensing,
    }


def llm_analysis(item: dict) -> dict | None:
    if not KEY:
        return None
    user = {k: item.get(k) for k in (
        "full_name", "description", "url", "language",
        "topics", "stars", "license", "category", "score",
    )}
    payload = {
        "model": MODEL,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
    }
    req = Request(
        API,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + KEY,
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return json.loads(content)
    except (HTTPError, URLError, KeyError, json.JSONDecodeError, TimeoutError) as exc:
        print(f"LLM analysis failed for {item.get('full_name')}: {exc}")
        return None


def _valid(result: dict | None) -> bool:
    if not isinstance(result, dict):
        return False
    if not result.get("what_it_does"):
        return False
    products = result.get("best_products") or result.get("business_opportunities") or []
    if not products or not isinstance(products[0], dict):
        return False
    return True


def analyze_item(item: dict) -> tuple[dict, str]:
    """Return (analysis_dict, source_tag)."""
    if not FORCE:
        existing_path = OUT / (item["full_name"].replace("/", "__") + ".json")
        if existing_path.exists():
            try:
                existing = json.loads(existing_path.read_text(encoding="utf-8"))
                if _valid(existing):
                    return existing, existing.get("_source", "external")
            except:
                pass

    result = llm_analysis(item)
    if _valid(result):
        result["_source"] = "llm"
        return result, "llm"

    fb = fallback(item)
    fb["_source"] = "fallback"
    return fb, "fallback"


def main() -> int:
    if not LATEST.exists():
        print("latest.json not found; run scan first.")
        return 1
    data = json.loads(LATEST.read_text(encoding="utf-8"))
    items = data.get("top", [])[:TOP_N]
    OUT.mkdir(parents=True, exist_ok=True)

    counts = {"llm": 0, "fallback": 0, "external": 0}
    for item in items:
        if not item.get("full_name"):
            continue
        analysis, source = analyze_item(item)
        filename = item["full_name"].replace("/", "__") + ".json"
        path = OUT / filename
        path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
        counts[source if source in counts else "external"] += 1

    print(
        f"analysis complete: {len(items)} repos; "
        f"llm={counts['llm']}, fallback={counts['fallback']}, kept_existing={counts['external']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())