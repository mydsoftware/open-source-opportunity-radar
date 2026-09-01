#!/usr/bin/env python3
"""ساخت صف تحلیل برای Freebuff؛ فقط پروژه‌های جدید/تغییرکرده را وارد صف می‌کند."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
latest = json.loads((ROOT / 'data' / 'latest.json').read_text(encoding='utf-8'))
out_dir = ROOT / 'data' / 'freebuff-queue'
out_dir.mkdir(parents=True, exist_ok=True)

queue = []
for item in latest.get('top', []):
    key = item['full_name'].replace('/', '__')
    case = ROOT / 'data' / 'business-cases' / f'{key}.json'
    if case.exists():
        continue
    queue.append({
        'repository': item['full_name'],
        'url': item['url'],
        'category': item.get('category'),
        'language': item.get('language'),
        'topics': item.get('topics', []),
        'description': item.get('description'),
        'score': item.get('score'),
        'stars': item.get('stars'),
        'license': item.get('license'),
        'task': 'Use .agents/open-source-opportunity-analyst.ts. Inspect this repository deeply and write the final structured analysis to data/business-cases/<owner>__<repo>.json. Do not reuse generic templates.'
    })

queue.sort(key=lambda x: (-float(x.get('score') or 0), -int(x.get('stars') or 0)))
(out_dir / 'queue.json').write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Freebuff queue: {len(queue)} repositories')
