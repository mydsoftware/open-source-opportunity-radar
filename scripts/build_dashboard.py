#!/usr/bin/env python3
"""Render the static Persian dashboard with inline AI analyses.

For each repository in `data/latest.json`, this script looks up a business
case in `data/business-cases/<owner>__<repo>.json`. If present, the analysis
is rendered inline; otherwise a "queued for analysis" message is shown.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CASES = DATA / "business-cases"


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


SOURCE_LABELS = {
    "llm": ("🤖 تحلیل AI داخلی", "#263b60"),
    "freebuff": ("🧠 تحلیل Agent", "#3d5a3d"),
    "fallback": ("⚙️ تحلیل خودکار", "#3d3d5a"),
    "external": ("📥 تحلیل خارجی", "#5a4d3d"),
}
WAITING = "این پروژه در صف تحلیل است؛ به‌محض آماده شدن تحلیل AI یا Agent، در همین بخش نمایش داده می‌شود."


def get_analysis(item: dict) -> dict:
    """Return a normalized analysis dict plus a source label."""
    path = CASES / (item.get("full_name", "").replace("/", "__") + ".json")
    if not path.exists():
        return {"_missing": True}
    payload = load(path, {})
    opps = payload.get("best_products") or payload.get("business_opportunities") or []
    fast = next(
        (o for o in opps if isinstance(o, dict) and ("هفته" in (o.get("time_to_money") or "") or "week" in (o.get("time_to_money") or "").lower())),
        opps[0] if opps else {},
    )
    long = next((o for o in opps if isinstance(o, dict) and o != fast), {})
    return {
        "use": payload.get("what_it_does") or WAITING,
        "problem": payload.get("problem_solved") or payload.get("why_it_matters") or WAITING,
        "fast_product": (fast.get("product") if isinstance(fast, dict) else None) or payload.get("best_path") or WAITING,
        "fast_customer": (fast.get("customer") if isinstance(fast, dict) else None) or payload.get("paying_customers") or WAITING,
        "fast_example": (fast.get("example_usage") if isinstance(fast, dict) else None) or WAITING,
        "fast_sell": (fast.get("sales_pitch") if isinstance(fast, dict) else None) or WAITING,
        "fast_money": (fast.get("monetization") if isinstance(fast, dict) else None) or WAITING,
        "fast_pricing": (fast.get("pricing") if isinstance(fast, dict) else None) or "تعیین نشده",
        "fast_local": (fast.get("localization") if isinstance(fast, dict) else None) or "—",
        "long_product": (long.get("product") if isinstance(long, dict) else None) or (payload.get("recommendation") or payload.get("long_term_path")) or WAITING,
        "long_customer": (long.get("customer") if isinstance(long, dict) else None) or "—",
        "long_money": (long.get("monetization") if isinstance(long, dict) else None) or "—",
        "long_time": (long.get("time_to_money") if isinstance(long, dict) else None) or "—",
        "long_diff": (long.get("difficulty") if isinstance(long, dict) else None) or "—",
        "recommendation": payload.get("recommendation") or payload.get("fastest_path") or WAITING,
        "confidence": payload.get("confidence"),
        "license_notes": (fast.get("license_risk") if isinstance(fast, dict) else None) or payload.get("license_notes") or "—",
        "source": payload.get("_source", "fallback"),
    }


CSS = """
*{box-sizing:border-box}
body{font-family:Tahoma,Arial,sans-serif;margin:0;background:#080d18;color:#e9eef8;line-height:1.8}
main{max-width:1250px;margin:auto;padding:28px 18px}
header,.filters,.project{background:#111a2b;border:1px solid #263653;border-radius:18px}
header{padding:28px;margin-bottom:20px}
h1{margin:0 0 8px;font-size:30px}
h2{margin:0;font-size:21px}
h4{margin:8px 0;font-size:15px;color:#dbe7ff}
.sub,.desc{color:#aab7ce}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:20px}
.stat{background:#18233a;padding:18px;border-radius:15px}
.stat b{font-size:28px;display:block}
.filters{padding:18px;margin:20px 0}
.filter,.sort{border:1px solid #314463;background:#18233a;color:#dce7f7;border-radius:999px;padding:8px 14px;margin:4px;cursor:pointer;font-family:inherit}
.filter.active,.filter:hover,.sort:hover{background:#263b60}
.search{width:100%;padding:12px 16px;margin:12px 0;border-radius:12px;border:1px solid #314463;background:#0d1525;color:#fff;font-family:inherit;font-size:15px}
.project{padding:20px;margin:16px 0}
.project.hidden{display:none}
.head{display:flex;justify-content:space-between;gap:20px}
.rank{color:#7f8da5;font-weight:bold}
a{color:#8db4ff;text-decoration:none}
.score{font-size:28px;font-weight:bold;white-space:nowrap}
.score small{font-size:13px;color:#7f8da5}
.facts{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
.facts span{background:#18233a;border-radius:999px;padding:5px 11px;color:#c7d2e5;font-size:13px}
.badge-row{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.badge{font-size:12px;padding:4px 10px;border-radius:999px;color:#fff}
.badge-queued{background:#5a3d3d;color:#fff;font-size:12px;padding:4px 10px;border-radius:999px}
.conf{font-size:12px;color:#aab7ce;align-self:center}
.analysis{margin-top:12px;background:#0d1525;border-radius:12px;padding:14px;display:grid;gap:10px}
.analysis p{margin:4px 0;color:#b8c4d8;font-size:14px}
.opps{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.opp{background:#111c30;border-radius:10px;padding:12px}
.opp.fast{border-right:3px solid #5878a8}
.opp.long{border-right:3px solid #a87a58}
.example{margin-top:8px;padding:8px;border-right:2px solid #5878a8;background:#0a111e;border-radius:6px;color:#d6e1f2;font-size:13px}
.rec{background:#111c30;border-radius:10px;padding:12px;border-right:3px solid #58a878}
.queued{background:#1a1418;border-radius:10px;padding:14px;color:#c0a8b8;font-size:14px;border-right:3px solid #a85878}
@media(max-width:900px){.opps{grid-template-columns:1fr}}
@media(max-width:600px){.stats{grid-template-columns:1fr}.head{display:block}.score{margin-top:10px}}
"""


def render_card(i: int, item: dict) -> str:
    a = get_analysis(item)
    cat = item.get("category") or "سایر"
    name = html.escape(item.get("full_name", "نامشخص"))
    url = html.escape(item.get("url", "#"))
    desc = html.escape(item.get("description") or "")
    lic = html.escape(item.get("license") or "نامشخص")
    score = item.get("score", 0)
    stars = item.get("stars", 0)

    if a.get("_missing"):
        badge = '<span class="badge badge-queued">⏳ در صف تحلیل</span>'
        analysis_html = f'<div class="queued"><p>{WAITING}</p></div>'
    else:
        src_label, src_color = SOURCE_LABELS.get(a["source"], SOURCE_LABELS["fallback"])
        conf = a.get("confidence")
        conf_html = f'<span class="conf">اعتماد تحلیل: <b>{conf}</b>/100</span>' if isinstance(conf, (int, float)) else ""
        badge = f'<span class="badge" style="background:{src_color}">{src_label}</span>{conf_html}'
        analysis_html = f"""
        <div class="analysis">
          <div class="analysis-block">
            <h4>📌 این پروژه واقعاً چه می‌کند</h4>
            <p>{html.escape(a['use'])}</p>
            <p><b>مسئله‌ای که حل می‌کند:</b> {html.escape(a['problem'])}</p>
          </div>
          <div class="opps">
            <div class="opp fast">
              <h4>🚀 فرصت اول: سریع‌ترین مسیر درآمد</h4>
              <p><b>محصول:</b> {html.escape(a['fast_product'])}</p>
              <p><b>مشتری هدف:</b> {html.escape(a['fast_customer'])}</p>
              <div class="example"><b>سناریوی واقعی:</b> {html.escape(a['fast_example'])}</div>
              <div class="example"><b>متن فروش:</b> {html.escape(a['fast_sell'])}</div>
              <p><b>مدل درآمد:</b> {html.escape(a['fast_money'])}</p>
              <p><b>قیمت‌گذاری:</b> {html.escape(a['fast_pricing'])}</p>
              <p><b>بومی‌سازی:</b> {html.escape(a['fast_local'])}</p>
            </div>
            <div class="opp long">
              <h4>🏗️ فرصت دوم: مسیر بلندمدت</h4>
              <p><b>محصول:</b> {html.escape(a['long_product'])}</p>
              <p><b>مشتری:</b> {html.escape(a['long_customer'])}</p>
              <p><b>درآمد:</b> {html.escape(a['long_money'])}</p>
              <p><b>زمان:</b> {html.escape(a['long_time'])} · <b>سختی:</b> {html.escape(a['long_diff'])}</p>
            </div>
          </div>
          <div class="rec">
            <h4>✅ توصیه نهایی</h4>
            <p>{html.escape(a['recommendation'])}</p>
            <p><b>ریسک لایسنس:</b> {html.escape(a['license_notes'])}</p>
          </div>
        </div>
        """

    return f"""
    <article class="project" data-category="{html.escape(cat)}" data-score="{score}" data-stars="{stars}">
      <div class="rank">#{i}</div>
      <div class="head">
        <div>
          <h2><a href="{url}" target="_blank" rel="noopener">{name}</a></h2>
          <p class="desc">{desc}</p>
          <div class="badge-row">{badge}</div>
        </div>
        <div class="score">{score}<small>/100</small></div>
      </div>
      <div class="facts"><span>⭐ {stars:,}</span><span>⚖️ {lic}</span><span>🏷️ {html.escape(cat)}</span></div>
      {analysis_html}
    </article>
    """


def render_page(data: dict) -> tuple[str, int]:
    cats: dict[str, int] = {}
    for x in data.get("top", []):
        c = x.get("category") or "سایر"
        cats[c] = cats.get(c, 0) + 1

    buttons = "".join(
        f'<button class="filter" data-cat="{html.escape(c)}">{html.escape(c)} <small>({n})</small></button>'
        for c, n in sorted(cats.items(), key=lambda z: (-z[1], z[0]))
    )

    cards = [render_card(i, x) for i, x in enumerate(data.get("top", []), 1)]

    llm_count = sum(
        1
        for x in data.get("top", [])
        if (CASES / (x.get("full_name", "").replace("/", "__") + ".json")).exists()
    )

    page = f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>رادار فرصت‌های درآمدی متن‌باز</title>
<style>{CSS}</style>
</head>
<body>
<main>
  <header>
    <h1>📡 رادار فرصت‌های درآمدی متن‌باز</h1>
    <div class="sub">تحلیل اختصاصی برای هر Repository؛ هر پروژه توسط AI یا Agent بررسی می‌شود.</div>
    <div class="stats">
      <div class="stat"><b>{data.get('count', 0)}</b>پروژه اسکن‌شده</div>
      <div class="stat"><b>{len(data.get('top', []))}</b>فرصت رتبه‌بندی‌شده</div>
      <div class="stat"><b>{llm_count}</b>تحلیل آماده</div>
    </div>
    <div class="sub">آخرین بروزرسانی: {html.escape(str(data.get('generated_at', '')))}</div>
  </header>
  <div class="filters">
    <h2>🗂️ دسته‌بندی و جست‌وجو</h2>
    <input id="search" class="search" placeholder="🔎 نام پروژه، تکنولوژی، مشتری یا حوزه...">
    <button class="filter active" data-cat="all">همه</button>
    {buttons}
    <div><b>مرتب‌سازی:</b><button class="sort" data-sort="score">⭐ امتیاز</button><button class="sort" data-sort="stars">🌟 ستاره</button></div>
  </div>
  <h1>🏆 فرصت‌های برتر</h1>
  {''.join(cards)}
</main>
<script>
const cards=[...document.querySelectorAll('.project')];
let cat='all',term='',sort='score';
function render(){{
  cards.sort((a,b)=>parseFloat(b.dataset[sort])-parseFloat(a.dataset[sort])).forEach(c=>c.parentNode.appendChild(c));
  const q=term.toLowerCase();
  cards.forEach(c=>c.classList.toggle('hidden',!((cat==='all'||c.dataset.category===cat)&&c.innerText.toLowerCase().includes(q))));
}}
document.querySelectorAll('.filter').forEach(b=>b.onclick=()=>{{
  document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');cat=b.dataset.cat;render();
}});
document.querySelector('#search').oninput=e=>{{term=e.target.value;render()}};
document.querySelectorAll('.sort').forEach(b=>b.onclick=()=>{{sort=b.dataset.sort;render()}});
render();
</script>
</body>
</html>
"""
    return page, llm_count


def main() -> int:
    data = load(DATA / "latest.json", {"generated_at": "هنوز اسکن نشده", "count": 0, "top": []})
    page, llm_count = render_page(data)
    out = ROOT / "dashboard" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Built dashboard: {len(data.get('top', []))} projects, {llm_count} AI/Agent analyses inline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())