#!/usr/bin/env python3
import json, html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
def load(p,d=None):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except:return d if d is not None else {}
data=load(DATA/'latest.json',{'generated_at':'هنوز اسکن نشده','count':0,'top':[]}); cases=DATA/'business-cases'

def get_analysis(x):
    a=load(cases/(x.get('full_name','').replace('/','__')+'.json'),{})
    opp=a.get('best_products') or a.get('business_opportunities') or []
    best=opp[0] if opp and isinstance(opp[0],dict) else {}
    waiting='تحلیل اختصاصی Freebuff هنوز برای این پروژه تولید نشده است.'
    return {
      'use':a.get('what_it_does') or waiting,
      'why':a.get('problem_solved') or a.get('why_it_matters') or waiting,
      'for_you':best.get('product') or a.get('best_path') or waiting,
      'customer':best.get('customer') or a.get('paying_customers') or waiting,
      'example':best.get('example_usage') or waiting,
      'sell':best.get('sales_pitch') or best.get('sales_pitch') or waiting,
      'money':best.get('monetization') or waiting,
      'features':best.get('localization') or waiting,
      'pricing':best.get('pricing') or 'برای این پروژه هنوز قیمت‌گذاری اختصاصی تعیین نشده است.',
      'fast':a.get('recommendation') or a.get('fastest_path') or waiting,
      'difficulty':best.get('difficulty') or 'نامشخص','time':best.get('time_to_money') or 'نامشخص','risk':best.get('license_risk') or a.get('license_notes') or 'بررسی شود'
    }

cats={}
for x in data.get('top',[]): c=x.get('category') or 'سایر'; cats[c]=cats.get(c,0)+1
buttons=''.join(f'<button class="filter" data-cat="{html.escape(c)}">{html.escape(c)} <small>({n})</small></button>' for c,n in sorted(cats.items(),key=lambda z:(-z[1],z[0])))
cards=[]
for i,x in enumerate(data.get('top',[]),1):
    a=get_analysis(x);cat=x.get('category') or 'سایر';name=html.escape(x.get('full_name','نامشخص'));url=html.escape(x.get('url','#'));desc=html.escape(x.get('description') or '');lic=html.escape(x.get('license') or 'نامشخص');score=x.get('score',0);stars=x.get('stars',0)
    cards.append(f'''<article class="project" data-category="{html.escape(cat)}" data-score="{score}" data-stars="{stars}"><div class="rank">#{i}</div><div class="head"><div><h2><a href="{url}" target="_blank" rel="noopener">{name}</a></h2><p class="desc">{desc}</p></div><div class="score">{score}<small>/100</small></div></div><div class="facts"><span>⭐ {stars:,}</span><span>⚖️ {lic}</span><span>🏷️ {html.escape(cat)}</span></div><div class="cols"><section><h3>💡 کاربرد پروژه</h3><p>{html.escape(a['use'])}</p><p><b>مسئله‌ای که حل می‌کند:</b> {html.escape(a['why'])}</p></section><section><h3>🎯 کاربرد برای شما</h3><p>{html.escape(a['for_you'])}</p><div class="example"><b>مثال واقعی استفاده:</b> {html.escape(a['example'])}</div><p><b>مشتری هدف:</b> {html.escape(a['customer'])}</p></section><section><h3>💰 مدل درآمدی پیشنهادی</h3><p><b>{html.escape(a['money'])}</b></p><p><b>قیمت‌گذاری پیشنهادی:</b> {html.escape(a['pricing'])}</p><p><b>بومی‌سازی:</b> {html.escape(a['features'])}</p><div class="example"><b>مثال فروش به مشتری:</b> {html.escape(a['sell'])}</div></section><section><h3>🚀 برنامه کسب درآمد</h3><p>{html.escape(a['fast'])}</p><p><b>سختی:</b> {html.escape(a['difficulty'])} · <b>زمان تا درآمد:</b> {html.escape(a['time'])}</p><p><b>ریسک لایسنس:</b> {html.escape(a['risk'])}</p></section></div></article>''')
css='''*{box-sizing:border-box}body{font-family:Tahoma,Arial,sans-serif;margin:0;background:#080d18;color:#e9eef8;line-height:1.8}main{max-width:1250px;margin:auto;padding:28px 18px}header,.filters,.project{background:#111a2b;border:1px solid #263653;border-radius:18px}header{padding:28px;margin-bottom:20px}h1{margin:0 0 8px;font-size:30px}h2{margin:0;font-size:21px}.sub,.desc{color:#aab7ce}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:20px}.stat{background:#18233a;padding:18px;border-radius:15px}.stat b{font-size:28px;display:block}.filters{padding:18px;margin:20px 0}.filter,.sort{border:1px solid #314463;background:#18233a;color:#dce7f7;border-radius:999px;padding:8px 14px;margin:4px;cursor:pointer;font-family:inherit}.filter.active,.filter:hover,.sort:hover{background:#263b60}.search{width:100%;padding:12px 16px;margin:12px 0;border-radius:12px;border:1px solid #314463;background:#0d1525;color:#fff;font-family:inherit;font-size:15px}.project{padding:20px;margin:16px 0}.project.hidden{display:none}.head{display:flex;justify-content:space-between;gap:20px}.rank{color:#7f8da5;font-weight:bold}a{color:#8db4ff;text-decoration:none}.score{font-size:28px;font-weight:bold;white-space:nowrap}.score small{font-size:13px;color:#7f8da5}.facts{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}.facts span{background:#18233a;border-radius:999px;padding:5px 11px;color:#c7d2e5;font-size:13px}.cols{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}section{background:#0d1525;padding:14px;border-radius:12px}section h3{font-size:15px;margin:0 0 7px;color:#dbe7ff}section p{margin:4px 0;color:#b8c4d8;font-size:14px}.example{margin-top:10px;padding:10px;border-right:3px solid #5878a8;background:#111c30;border-radius:8px;color:#d6e1f2;font-size:13px}@media(max-width:900px){.cols{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.stats,.cols{grid-template-columns:1fr}.head{display:block}.score{margin-top:10px}}'''
page=f'''<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>رادار فرصت‌های درآمدی متن‌باز</title><style>{css}</style></head><body><main><header><h1>📡 رادار فرصت‌های درآمدی متن‌باز</h1><div class="sub">تحلیل اختصاصی Freebuff برای هر Repository؛ کاربرد واقعی، محصول، مشتری، مثال فروش و مدل درآمدی.</div><div class="stats"><div class="stat"><b>{data.get('count',0)}</b>پروژه اسکن‌شده</div><div class="stat"><b>{len(data.get('top',[]))}</b>فرصت رتبه‌بندی‌شده</div><div class="stat"><b>{len(cats)}</b>دسته‌بندی</div></div><div class="sub">آخرین بروزرسانی: {html.escape(str(data.get('generated_at','')))}</div></header><div class="filters"><h2>🗂️ دسته‌بندی و جست‌وجو</h2><input id="search" class="search" placeholder="🔎 نام پروژه، تکنولوژی، مشتری یا حوزه..."><button class="filter active" data-cat="all">همه</button>{buttons}<div><b>مرتب‌سازی:</b><button class="sort" data-sort="score">⭐ امتیاز</button><button class="sort" data-sort="stars">🌟 ستاره</button></div></div><h1>🏆 فرصت‌های برتر</h1>{''.join(cards)}</main><script>const cards=[...document.querySelectorAll('.project')];let cat='all',term='',sort='score';function render(){{cards.sort((a,b)=>parseFloat(b.dataset[sort])-parseFloat(a.dataset[sort])).forEach(c=>c.parentNode.appendChild(c));const q=term.toLowerCase();cards.forEach(c=>c.classList.toggle('hidden',!((cat==='all'||c.dataset.category===cat)&&c.innerText.toLowerCase().includes(q))))}}document.querySelectorAll('.filter').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');cat=b.dataset.cat;render()}});document.querySelector('#search').oninput=e=>{{term=e.target.value;render()}};document.querySelectorAll('.sort').forEach(b=>b.onclick=()=>{{sort=b.dataset.sort;render()}});render();</script></main></body></html>'''
out=ROOT/'dashboard'/'index.html';out.parent.mkdir(exist_ok=True);out.write_text(page,encoding='utf-8');print(f'Built dashboard: {len(cards)} projects, Freebuff-compatible analysis reader enabled.')
