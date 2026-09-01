#!/usr/bin/env python3
"""تحلیل اختصاصی فرصت کسب‌وکار برای هر Repository؛ LLM اختیاری و fallback پایدار."""
import json, os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
API = os.getenv('LLM_BASE_URL', 'https://openrouter.ai/api/v1').rstrip('/') + '/chat/completions'
KEY = os.getenv('LLM_API_KEY', '')
MODEL = os.getenv('LLM_MODEL', 'openai/gpt-oss-20b:free')
OUT = ROOT / 'data' / 'business-cases'

PROMPT = """
تو تحلیلگر ارشد Open Source و Product/Business هستی.
Repository داده‌شده را فقط بر اساس اطلاعات واقعی همان Repository تحلیل کن.
تمام متن‌ها باید فارسی باشند و تحلیل باید مخصوص همان Repository باشد.
نام Repository، توضیح، زبان، Topics و قابلیت واقعی آن را در تحلیل لحاظ کن.
برای Repositoryهای مختلف متن تکراری تولید نکن.
خروجی فقط JSON معتبر با این کلیدها باشد:
what_it_does, why_it_matters, best_path, business_opportunities,
missing_features, paying_customers, fastest_path, long_term_path,
confidence, license_notes
business_opportunities حداکثر 3 مورد و هر مورد شامل:
product, customer, monetization, example_usage, sales_pitch,
localization, difficulty, time_to_money, license_risk
هیچ درآمدی را تضمین نکن.
"""


def fallback(item):
    name = item.get('full_name') or 'این پروژه'
    description = item.get('description') or 'توضیح کافی در GitHub ثبت نشده است.'
    category = item.get('category') or 'سایر'
    language = item.get('language') or 'نامشخص'
    topics = item.get('topics') or []
    topics_text = '، '.join(topics[:6]) if topics else category
    license_name = item.get('license') or 'نامشخص'

    product = f'یک محصول یا سرویس تخصصی بر پایه قابلیت واقعی «{name}» برای حوزه {category}.'
    customer = f'کسب‌وکارها و تیم‌هایی که به قابلیت «{name}» در حوزه {category} نیاز دارند.'
    example = f'مثلاً قابلیت اصلی «{name}» را در یک پنل فارسی قرار بده تا مشتری بتواند بدون کار با کد از آن استفاده کند.'
    pitch = f'«ما قابلیت {name} را متناسب با نیاز کسب‌وکار شما آماده، فارسی‌سازی و راه‌اندازی می‌کنیم و پشتیبانی هم ارائه می‌دهیم.»'

    return {
        'what_it_does': f'«{name}» یک پروژه در حوزه {category} است. توضیح ثبت‌شده: {description} زبان: {language}. موضوعات مرتبط: {topics_text}.',
        'why_it_matters': f'قابلیت اصلی «{name}» می‌تواند از یک ابزار فنی به یک محصول آماده برای کاربران حوزه {category} تبدیل شود.',
        'best_path': product,
        'business_opportunities': [{
            'product': product,
            'customer': customer,
            'monetization': 'هزینه راه‌اندازی + اشتراک ماهانه + سفارشی‌سازی + پشتیبانی.',
            'example_usage': example,
            'sales_pitch': pitch,
            'localization': 'رابط فارسی و RTL، آموزش فارسی، پنل ساده و اتصال به سرویس‌های موردنیاز بازار هدف.',
            'difficulty': 'متوسط',
            'time_to_money': 'حدود ۱ تا ۴ هفته برای MVP خدماتی؛ وابسته به پیچیدگی پروژه.',
            'license_risk': f'لایسنس: {license_name}. قبل از استفاده تجاری، LICENSE و NOTICE و وابستگی‌ها بررسی شوند.'
        }],
        'missing_features': ['رابط فارسی و RTL', 'پنل مناسب کاربر غیر فنی', 'مستندات و آموزش فارسی', 'اتصال به سرویس‌های بازار هدف'],
        'paying_customers': customer,
        'fastest_path': f'یک MVP کوچک با قابلیت واقعی «{name}» برای یک مشتری حوزه {category} بساز و ابتدا هزینه راه‌اندازی و سفارشی‌سازی دریافت کن.',
        'long_term_path': f'بعد از اثبات تقاضا، محصول مبتنی بر «{name}» را به SaaS تخصصی حوزه {category} تبدیل کن.',
        'confidence': 55,
        'license_notes': f'لایسنس فعلی: {license_name}. پیش از فروش، شرایط مجوز و وابستگی‌ها بررسی شوند.'
    }


def llm_analysis(item):
    user = {k: item.get(k) for k in ('full_name', 'description', 'url', 'language', 'topics', 'stars', 'license', 'category', 'score')}
    payload = {
        'model': MODEL,
        'temperature': 0.15,
        'response_format': {'type': 'json_object'},
        'messages': [
            {'role': 'system', 'content': PROMPT},
            {'role': 'user', 'content': json.dumps(user, ensure_ascii=False)}
        ]
    }
    req = Request(API, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers={
        'Authorization': 'Bearer ' + KEY,
        'Content-Type': 'application/json'
    })
    with urlopen(req, timeout=90) as response:
        body = json.loads(response.read().decode('utf-8'))
    content = body['choices'][0]['message']['content']
    return json.loads(content)


def main():
    latest = ROOT / 'data' / 'latest.json'
    data = json.loads(latest.read_text(encoding='utf-8'))
    OUT.mkdir(parents=True, exist_ok=True)
    items = data.get('top', [])[:100]

    for item in items:
        result = None
        if KEY:
            try:
                result = llm_analysis(item)
                if not isinstance(result, dict) or not result.get('what_it_does') or not result.get('business_opportunities'):
                    result = None
            except Exception as exc:
                print(f'LLM analysis failed for {item.get("full_name")}: {exc}')

        if result is None:
            result = fallback(item)
            result['_source'] = 'repository_specific_fallback'
        else:
            result['_source'] = 'llm'

        filename = item['full_name'].replace('/', '__') + '.json'
        (OUT / filename).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'business analysis complete: {len(items)} repositories')


if __name__ == '__main__':
    main()
