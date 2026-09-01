#!/usr/bin/env python3
"""اعتبارسنجی و وارد کردن خروجی‌های Freebuff به عنوان business case."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'data' / 'business-cases'
QUEUE = ROOT / 'data' / 'freebuff-queue' / 'queue.json'

REQUIRED = {'what_it_does', 'problem_solved', 'why_it_matters', 'best_products', 'recommendation'}
PRODUCT_REQUIRED = {'product','customer','example_usage','sales_pitch','monetization','pricing','localization','difficulty','time_to_money','license_risk'}


def valid(data):
    if not REQUIRED.issubset(data): return False
    if not isinstance(data['best_products'], list) or not data['best_products']: return False
    for p in data['best_products'][:3]:
        if not isinstance(p, dict) or not PRODUCT_REQUIRED.issubset(p): return False
    return True


def main():
    CASES.mkdir(parents=True, exist_ok=True)
    queue = json.loads(QUEUE.read_text(encoding='utf-8')) if QUEUE.exists() else []
    imported = 0
    invalid = []
    for item in queue:
        path = CASES / (item['repository'].replace('/', '__') + '.json')
        if not path.exists():
            invalid.append(item['repository'])
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            invalid.append(item['repository']); continue
        if not valid(data):
            invalid.append(item['repository']); continue
        data['_source'] = 'freebuff'
        data['_repository'] = item['repository']
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        imported += 1
    print(f'Freebuff results validated: {imported}; pending/invalid: {len(invalid)}')
    if invalid:
        print('Pending:', ', '.join(invalid[:30]))


if __name__ == '__main__': main()
