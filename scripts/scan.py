#!/usr/bin/env python3
from __future__ import annotations
import json, os, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import yaml

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'radar.sqlite3'
REPORTS = ROOT / 'reports'
API = 'https://api.github.com'
TOKEN = os.getenv('GITHUB_TOKEN', '')
HEAD = {'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
if TOKEN: HEAD['Authorization'] = f'Bearer {TOKEN}'

def gh(path):
    req = Request(API + path, headers=HEAD)
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def init(c):
    DB.parent.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    c.executescript('''CREATE TABLE IF NOT EXISTS repositories(id INTEGER PRIMARY KEY,full_name TEXT UNIQUE,name TEXT,url TEXT,description TEXT,language TEXT,license TEXT,topics TEXT,category TEXT,discovered_at TEXT,updated_at TEXT);CREATE TABLE IF NOT EXISTS snapshots(id INTEGER PRIMARY KEY AUTOINCREMENT,repo_id INTEGER,scanned_at TEXT,stars INTEGER,forks INTEGER,watchers INTEGER,open_issues INTEGER,pushed_at TEXT,updated_at TEXT);CREATE TABLE IF NOT EXISTS opportunities(repo_id INTEGER PRIMARY KEY,scanned_at TEXT,score REAL,growth_score REAL,license_score REAL,market_score REAL,saas_score REAL,ai_score REAL,localization_score REAL,best_path TEXT,fastest_path TEXT,long_term_path TEXT,rationale TEXT);CREATE TABLE IF NOT EXISTS scan_runs(id INTEGER PRIMARY KEY AUTOINCREMENT,started_at TEXT,finished_at TEXT,repos_found INTEGER,errors INTEGER);''')

def lscore(l):
    return {'MIT':100,'Apache-2.0':95,'BSD-2-Clause':95,'BSD-3-Clause':95,'ISC':95,'MPL-2.0':75,'LGPL-3.0':65,'LGPL-2.1':65,'GPL-3.0':55,'GPL-2.0':55,'AGPL-3.0':45,'SSPL-1.0':20,'BSL-1.1':25,None:10}.get(l,40)

def analyze(r, cat, growth):
    ls = lscore((r.get('license') or {}).get('spdx_id')); stars = r.get('stargazers_count',0); forks = r.get('forks_count',0)
    pop = min(100,20+stars**.5*2.2); community = min(100,20+forks**.5*2.5); activity = 90 if r.get('pushed_at') else 20
    market = {'AI':95,'Automation':92,'E-commerce':90,'Business':90,'Documents':89,'Low-code':90,'IoT':88,'Analytics':87,'Developer':86,'Games':84,'Finance':84,'Web':82}.get(cat,75)
    text = (r.get('name','')+' '+(r.get('description') or '')).lower(); ai = 95 if cat=='AI' else (80 if any(x in text for x in ('ai','llm','agent','rag')) else 45)
    saas = min(98,market+(8 if cat in {'AI','Automation','Business','E-commerce','Documents','Analytics','Low-code'} else 0)); loc = 88 if cat in {'Business','E-commerce','Documents','Finance','Analytics','Education'} else 62
    total = pop*.10+growth*.15+activity*.10+community*.05+75*.10+ls*.15+market*.10+saas*.10+ai*.05+loc*.05
    if cat=='AI': paths=('AI SaaS','Integration + Customization','AI Platform')
    elif cat in {'Business','E-commerce','Documents','Analytics','Low-code'}: paths=('Vertical SaaS','Installation + Customization','Enterprise SaaS')
    elif cat in {'IoT','Developer'}: paths=('Managed Service','Setup + Support','Enterprise Platform')
    else: paths=('SaaS / Services','Installation + Customization','Platform / Enterprise')
    return round(total,1),round(growth,1),ls,market,saas,ai,loc,*paths

def main():
    started = datetime.now(timezone.utc).isoformat(); cfg = yaml.safe_load((ROOT/'config/discovery.yml').read_text()); DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB); c = conn.cursor(); init(c); found={}; errors=0
    for q in cfg['queries']:
        try:
            path=f"/search/repositories?q={quote(q['query']+' stars:>='+str(cfg['limits'].get('min_stars',100)))}&sort=stars&order=desc&per_page={cfg['limits'].get('per_query',20)}"
            for r in gh(path).get('items',[]): found[r['id']] = (r,q['category'])
        except Exception as e: errors += 1; print('discovery error',q['name'],e)
        time.sleep(.15)
    rows=[]; now=datetime.now(timezone.utc).isoformat()
    for r,cat in list(found.values())[:cfg['limits'].get('max_repositories',250)]:
        c.execute('SELECT stars FROM snapshots WHERE repo_id=? ORDER BY id DESC LIMIT 1',(r['id'],)); prev=c.fetchone(); growth=50 if not prev else max(0,min(100,50+(r['stargazers_count']-prev[0])*100/max(prev[0],1)))
        lic=(r.get('license') or {}).get('spdx_id'); c.execute('SELECT discovered_at FROM repositories WHERE id=?',(r['id'],)); old=c.fetchone(); discovered=old[0] if old and old[0] else now
        c.execute('INSERT OR REPLACE INTO repositories VALUES(?,?,?,?,?,?,?,?,?,?,?)',(r['id'],r['full_name'],r['name'],r['html_url'],r.get('description'),r.get('language'),lic,json.dumps(r.get('topics',[])),cat,discovered,now)); a=analyze(r,cat,growth); total,g,ls,mkt,saas,ai,loc,best,fast,long=a
        c.execute('INSERT INTO snapshots(repo_id,scanned_at,stars,forks,watchers,open_issues,pushed_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(r['id'],now,r['stargazers_count'],r['forks_count'],r['watchers_count'],r['open_issues_count'],r.get('pushed_at'),r.get('updated_at')))
        c.execute('INSERT OR REPLACE INTO opportunities VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(r['id'],now,total,g,ls,mkt,saas,ai,loc,best,fast,long,'Metadata-based opportunity hypothesis; not a revenue guarantee.')); rows.append((total,r,g,lic,best,fast,long))
    conn.commit(); rows.sort(reverse=True,key=lambda x:x[0]); lines=['# Open Source Opportunity Radar','',f'Generated: {now}',f'Repositories scanned: {len(rows)}','','## Top Opportunities','']
    for i,(s,r,g,lic,best,fast,long) in enumerate(rows[:100],1): lines += [f'### {i}. [{r["full_name"]}]({r["html_url"]}) — {s}/100',f'- Description: {r.get("description") or "N/A"}',f'- Stars: {r["stargazers_count"]:,} | Forks: {r["forks_count"]:,} | Growth signal: {g:.1f}',f'- License: {lic or "Unknown"}',f'- Best: **{best}** | Fastest: **{fast}** | Long-term: **{long}**','']
    (REPORTS/'latest.md').write_text('\n'.join(lines),encoding='utf-8'); (ROOT/'data/latest.json').write_text(json.dumps({'generated_at':now,'count':len(rows),'top':[{'full_name':r['full_name'],'url':r['html_url'],'score':s,'stars':r['stargazers_count'],'license':lic,'best_path':best} for s,r,g,lic,best,fast,long in rows[:100]]},ensure_ascii=False,indent=2),encoding='utf-8')
    finished=datetime.now(timezone.utc).isoformat(); c.execute('INSERT INTO scan_runs VALUES(NULL,?,?,?,?)',(started,finished,len(rows),errors)); conn.commit(); conn.close(); print(f'scan complete: {len(rows)} repositories, {errors} errors')
if __name__=='__main__': main()
