#!/usr/bin/env python3
import json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data_file = ROOT / 'data/latest.json'
data = json.loads(data_file.read_text(encoding='utf-8')) if data_file.exists() else {'generated_at': 'هنوز اسکن نشده', 'count': 0, 'top': []}


def profile(x):
    text = ((x.get('description') or '') + ' ' + (x.get('full_name') or '') + ' ' + (x.get('category') or '')).lower()
    if any(k in text for k in ('agent', 'llm', 'rag', 'ai', 'artificial intelligence', 'ollama', 'openhands')):
        return {'use':'برای ساخت ابزارهای هوش مصنوعی، Agent و قابلیت‌های LLM استفاده می‌شود.', 'for_you':'هسته پروژه را به یک محصول فارسی و ساده برای یک مشکل واقعی کسب‌وکار تبدیل کن.', 'customer':'فروشگاه‌ها، شرکت‌ها، تیم‌های فروش و پشتیبانی.', 'example':'مثلاً Agent را به سایت فروشگاه وصل کن تا محصول پیدا کند، به مشتری پاسخ بدهد و گزارش فروش بسازد.', 'sell':'به مشتری بگو: «برای کسب‌وکار شما یک دستیار هوش مصنوعی اختصاصی می‌سازیم که به اطلاعات خودتان متصل است.»', 'money':'SaaS اشتراکی + هزینه راه‌اندازی + API + Enterprise + پشتیبانی.', 'product':'فارسی و RTL، پنل ساده، مدل‌های رایگان/ارزان، اتصال به سایت و سرویس‌های محلی.', 'fast':'اول برای یک مشتری نسخه سفارشی بفروش؛ بعد قابلیت‌های مشترک را SaaS کن.', 'risk':'متوسط تا بالا'}
    if any(k in text for k in ('trading', 'stock', 'finance', 'crypto', 'investment')):
        return {'use':'برای تحلیل داده‌های مالی و ساخت ابزارهای کمکی تصمیم‌گیری استفاده می‌شود.', 'for_you':'آن را به داشبورد فارسی، ابزار تحلیل یا سیستم هشدار تبدیل کن.', 'customer':'معامله‌گران، تحلیلگران و شرکت‌های مالی.', 'example':'مثلاً قیمت‌ها و شاخص‌ها را جمع کن و هنگام رخداد شرایط مشخص به کاربر هشدار بده.', 'sell':'به مشتری بگو: «یک داشبورد تحلیل و هشدار اختصاصی برای بازار شما می‌سازیم.»', 'money':'اشتراک ماهانه + API + گزارش حرفه‌ای + پلن سازمانی.', 'product':'داده فارسی، تقویم شمسی، هشدار و داشبورد.', 'fast':'با داشبورد و گزارش تخصصی شروع کن و بعد SaaS بساز.', 'risk':'بالا'}
    if any(k in text for k in ('ecommerce', 'commerce', 'shop', 'store', 'woocommerce', 'shopify')):
        return {'use':'برای ساخت یا مدیریت فروشگاه، محصول، سفارش و عملیات فروش آنلاین استفاده می‌شود.', 'for_you':'یک نسخه فارسی و بومی برای نیاز فروشگاه‌های ایرانی بساز.', 'customer':'فروشگاه‌ها و کسب‌وکارهای آنلاین.', 'example':'مثلاً ابزار مدیریت سفارش با فاکتور فارسی و پیامک وضعیت سفارش بساز.', 'sell':'به مشتری بگو: «فروشگاه شما را فارسی‌سازی و با امکانات موردنیازتان اختصاصی می‌کنیم.»', 'money':'SaaS + هزینه راه‌اندازی + افزونه‌های پولی + پشتیبانی.', 'product':'RTL، تقویم شمسی، درگاه ایرانی، پیامک و فاکتور.', 'fast':'ابتدا نصب و سفارشی‌سازی بفروش؛ بعد SaaS کن.', 'risk':'متوسط'}
    if any(k in text for k in ('game', 'gaming', 'unity', 'godot', 'unreal')):
        return {'use':'برای ساخت بازی، ابزار بازی‌سازی یا Asset استفاده می‌شود.', 'for_you':'هسته پروژه را برای یک بازی یا ابزار بومی و قابل فروش استفاده کن.', 'customer':'بازیکنان، استودیوها و بازی‌سازها.', 'example':'مثلاً یک بازی موبایلی فارسی یا بسته UI/Asset آماده تولید کن و در مارکت بفروش.', 'sell':'به مشتری بگو: «این محصول آماده زمان تولید بازی شما را کم می‌کند و قابل شخصی‌سازی است.»', 'money':'فروش بازی + DLC/Asset + اشتراک ابزار + خدمات.', 'product':'فارسی‌سازی، محتوای بومی و UI راست‌به‌چپ.', 'fast':'یک محصول کوچک قابل فروش منتشر کن و از بازار بازخورد بگیر.', 'risk':'متوسط'}
    return {'use':x.get('description') or 'یک پروژه متن‌باز برای حل یک مسئله نرم‌افزاری مشخص.', 'for_you':'بخش قابل استفاده پروژه را به نسخه فارسی، تخصصی یا سرویس مدیریت‌شده تبدیل کن.', 'customer':'افراد و کسب‌وکارهایی که برای راه‌حل آماده پول می‌دهند.', 'example':'مثلاً قابلیت اصلی پروژه را بردار، رابط فارسی اضافه کن و آن را به‌صورت سرویس آماده بفروش.', 'sell':'به مشتری بگو: «این راه‌حل را برای نیاز شما آماده، فارسی‌سازی و نصب می‌کنیم.»', 'money':'نصب و سفارشی‌سازی + پشتیبانی + SaaS تخصصی.', 'product':'فارسی‌سازی، RTL، مستندات و اتصال به سرویس‌های محلی.', 'fast':'با یک پروژه سفارشی پولی شروع کن؛ سپس محصول تکرارپذیر بساز.', 'risk':'متوسط'}


categories = {}
for item in data.get('top', []):
    cat = item.get('category') or 'سایر'
    categories[cat] = categories.get(cat, 0) + 1

buttons = ''.join('<button class="filter" data-cat="{}">{} <small>({})</small></button>'.format(html.escape(k), html.escape(k), v) for k, v in sorted(categories.items(), key=lambda z: (-z[1], z[0])))

cards = []
for i, x in enumerate(data.get('top', []), 1):
    p = profile(x)
    cat = x.get('category') or 'سایر'
    url = html.escape(x.get('url', '#'))
    name = html.escape(x.get('full_name', 'نامشخص'))
    desc = html.escape(x.get('description') or p['use'])
    license_name = html.escape(x.get('license') or 'نامشخص')
    score = x.get('score', 0)
    stars = x.get('stars', 0)
    cards.append(f'''<article class="project" data-category="{html.escape(cat)}" data-score="{score}" data-stars="{stars}">
<div class="rank">#{i}</div><div class="head"><div><h2><a href="{url}" target="_blank" rel="noopener">{name}</a></h2><p class="desc">{desc}</p></div><div class="score">{score}<small>/100</small></div></div>
<div class="facts"><span>⭐ {stars:,}</span><span>⚖️ {license_name}</span><span>🏷️ {html.escape(cat)}</span><span>💰 {html.escape(x.get('best_path') or p['money'])}</span></div>
<div class="cols"><section><h3>💡 کاربرد پروژه</h3><p>{html.escape(p['use'])}</p></section><section><h3>🎯 کاربرد برای شما</h3><p>{html.escape(p['for_you'])}</p><div class="example"><b>مثال:</b> {html.escape(p['example'])}</div><p><b>مشتری هدف:</b> {html.escape(p['customer'])}</p></section><section><h3>💰 مدل درآمدی پیشنهادی</h3><p><b>{html.escape(p['money'])}</b></p><p>{html.escape(p['product'])}</p><div class="example"><b>چطور به مشتری بفروشی:</b> {html.escape(p['sell'])}</div></section><section><h3>🚀 برنامه کسب درآمد</h3><p>{html.escape(p['fast'])}</p><p>ریسک: <b>{html.escape(p['risk'])}</b></p></section></div></article>''')

html_doc = '''<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="رادار فرصت‌های درآمدزایی از پروژه‌های متن‌باز گیت‌هاب"><title>رادار فرصت‌های درآمدی متن‌باز</title><style>
*{box-sizing:border-box}body{font-family:Tahoma,Arial,sans-serif;margin:0;background:#080d18;color:#e9eef8;line-height:1.8}main{max-width:1250px;margin:auto;padding:28px 18px}header,.filters,.project{background:#111a2b;border:1px solid #263653;border-radius:18px}header{padding:28px;margin-bottom:20px}h1{margin:0 0 8px;font-size:30px}.sub{color:#aab7ce}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:20px}.stat{background:#18233a;padding:18px;border-radius:15px}.stat b{font-size:28px;display:block}.filters{padding:18px;margin:20px 0}.filter,.sort{border:1px solid #314463;background:#18233a;color:#dce7f7;border-radius:999px;padding:8px 14px;margin:4px;cursor:pointer;font-family:inherit}.filter.active,.filter:hover,.sort:hover{background:#263b60}.search{width:100%;padding:12px 16px;margin:12px 0;border-radius:12px;border:1px solid #314463;background:#0d1525;color:#fff;font-family:inherit;font-size:15px}.project{padding:20px;margin:16px 0}.project.hidden{display:none}.head{display:flex;justify-content:space-between;gap:20px}.rank{color:#7f8da5;font-weight:bold}h2{margin:0;font-size:21px}a{color:#8db4ff;text-decoration:none}.desc{color:#aab7ce}.score{font-size:28px;font-weight:bold;white-space:nowrap}.score small{font-size:13px;color:#7f8da5}.facts{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}.facts span{background:#18233a;border-radius:999px;padding:5px 11px;color:#c7d2e5;font-size:13px}.cols{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}section{background:#0d1525;padding:14px;border-radius:12px}section h3{font-size:15px;margin:0 0 7px;color:#dbe7ff}section p{margin:4px 0;color:#b8c4d8;font-size:14px}.example{margin-top:10px;padding:10px;border-right:3px solid #5878a8;background:#111c30;border-radius:8px;color:#d6e1f2;font-size:13px}.note{color:#8796ae;font-size:12px;margin-top:20px}@media(max-width:900px){.cols{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.stats,.cols{grid-template-columns:1fr}.head{display:block}.score{margin-top:10px}}</style></head><body><main><header><h1>📡 رادار فرصت‌های درآمدی متن‌باز</h1><div class="sub">هر پروژه را ساده و عملی بررسی کن: کاربرد، مشتری، مثال استفاده و مسیر درآمد.</div><div class="stats"><div class="stat"><b>__COUNT__</b>پروژه اسکن‌شده</div><div class="stat"><b>__TOP__</b>فرصت رتبه‌بندی‌شده</div><div class="stat"><b>__CATS__</b>دسته‌بندی</div></div><div class="sub">آخرین بروزرسانی: __UPDATED__</div></header><div class="filters"><h2>🗂️ دسته‌بندی و جست‌وجو</h2><input id="search" class="search" placeholder="🔎 نام پروژه، توضیحات یا دسته‌بندی را جست‌وجو کن..."><button class="filter active" data-cat="all">همه</button>__BUTTONS__<div><b>مرتب‌سازی:</b><button class="sort" data-sort="score">⭐ امتیاز درآمدی</button><button class="sort" data-sort="stars">🌟 بیشترین ستاره</button></div></div><h1>🏆 فرصت‌های برتر</h1>__CARDS__<p class="note">تحلیل کسب‌وکار یک فرضیه است، نه تضمین درآمد. پیش از استفاده تجاری، LICENSE، NOTICE، وابستگی‌ها و علائم تجاری پروژه بررسی شوند.</p></main><script>
const cards=[...document.querySelectorAll('.project')];let cat='all',term='',sort='score';function render(){cards.sort((a,b)=>parseFloat(b.dataset[sort])-parseFloat(a.dataset[sort]));const q=term.toLowerCase();cards.forEach(c=>{const ok=(cat==='all'||c.dataset.category===cat)&&c.innerText.toLowerCase().includes(q);c.classList.toggle('hidden',!ok);c.parentNode.appendChild(c)})}document.querySelectorAll('.filter').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');cat=b.dataset.cat;render()}));document.querySelector('#search').addEventListener('input',e=>{term=e.target.value;render()});document.querySelectorAll('.sort').forEach(b=>b.addEventListener('click',()=>{sort=b.dataset.sort;render()}));render();</script></body></html>'''

html_doc = html_doc.replace('__COUNT__', str(data.get('count', 0)))
html_doc = html_doc.replace('__TOP__', str(len(data.get('top', []))))
html_doc = html_doc.replace('__CATS__', str(len(categories)))
html_doc = html_doc.replace('__UPDATED__', html.escape(data.get('generated_at', '')))
html_doc = html_doc.replace('__BUTTONS__', buttons)
html_doc = html_doc.replace('__CARDS__', ''.join(cards))

out = ROOT / 'dashboard' / 'index.html'
out.parent.mkdir(exist_ok=True)
out.write_text(html_doc, encoding='utf-8')
print(f'dashboard built: {len(cards)} cards, {len(categories)} categories')
