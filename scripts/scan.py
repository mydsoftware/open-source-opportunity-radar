#!/usr/bin/env python3
"""Daily GitHub discovery, snapshots, change detection and business scoring."""
from __future__ import annotations
import json, os, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import yaml

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "radar.sqlite3"
REPORTS = ROOT / "reports"
API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "")


def gh(path: str):
    req = Request(API + path, headers={"Accept":"application/vnd.github+json", "X-GitHub-Api-Version":"2022-11-28", **({"Authorization":f"Bearer {TOKEN}"} if TOKEN else {})})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def db_init(c):
    c.executescript("""
    CREATE TABLE IF NOT EXISTS repositories(
      id INTEGER PRIMARY KEY, full_name TEXT UNIQUE, name TEXT, url TEXT, description TEXT,
      language TEXT, license TEXT, topics TEXT, category TEXT, discovered_at TEXT, updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS snapshots(
      id INTEGER PRIMARY KEY AUTOINCREMENT, repo_id INTEGER, scanned_at TEXT, stars INTEGER,
      forks INTEGER, watchers INTEGER, open_issues INTEGER, subscribers INTEGER,
      pushed_at TEXT, updated_at TEXT, default_branch TEXT, size_kb INTEGER,
      FOREIGN KEY(repo_id) REFERENCES repositories(id)
    );
    CREATE TABLE IF NOT EXISTS opportunities(
      repo_id INTEGER PRIMARY KEY, scanned_at TEXT, score REAL, confidence REAL,
      growth_score REAL, license_score REAL, market_score REAL, saas_score REAL,
      ai_score REAL, localization_score REAL, best_path TEXT, fastest_path TEXT,
      long_term_path TEXT, rationale TEXT, FOREIGN KEY(repo_id) REFERENCES repositories(id)
    );
    CREATE TABLE IF NOT EXISTS scan_runs(id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT, finished_at TEXT, repos_found INTEGER, errors INTEGER);
    """)


def score(repo, category, license_score):
    stars = repo.get("stargazers_count", 0)
    forks = repo.get("forks_count", 0)
    issues = repo.get("open_issues_count", 0)
    popularity = min(100, 20 + (stars ** 0.5) * 2.2)
    community = min(100, 20 + (forks ** 0.5) * 2.5)
    activity = 80 if repo.get("pushed_at") else 20
    growth = 50
    market = {"AI":90,"Automation":92,"E-commerce":88,"Business":88,"Documents":88,"IoT":87,"Analytics":86,"Developer":86,"Games":84,"Finance":84,"Low-code":90,"Web":82}.get(category,75)
    ai = 95 if category == "AI" else (80 if any(x in (repo.get("name","")+" "+(repo.get("description") or "")).lower() for x in ["ai","llm","agent","rag"]) else 45)
    saas = min(95, market + (10 if category in {"AI","Automation","Business","E-commerce","Documents","Analytics","Low-code"} else 0))
    localization = 85 if category in {"Business","E-commerce","Documents","Finance","Education","Analytics"} else 60
    total = (popularity*.10 + growth*.15 + activity*.10 + community*.05 + 70*.10 + license_score*.15 + market*.10 + saas*.10 + ai*.05 + localization*.05)
    if category == "AI": best, fast, long = "AI SaaS", "Integration + Customization", "AI Platform"
    elif category in {"Business","E-commerce","Documents","Analytics"}: best, fast, long = "Vertical SaaS", "Installation + Customization", "Enterprise SaaS"
    elif category in {"IoT","Developer"}: best, fast, long = "Managed Service", "Setup + Support", "Enterprise Platform"
    else: best, fast, long = "SaaS / Services", "Installation + Customization", "Platform / Enterprise"
    return round(total,1), round(min(99, 55 + license_score*.35),1), round(growth,1), round(market,1), round(saas,1), round(ai,1), round(localization,1), best, fast, long


def main():
    started = datetime.now(timezone.utc).isoformat()
    cfg = yaml.safe_load((ROOT/"config/discovery.yml").read_text())
    limits = cfg.get("limits", {})
    conn = sqlite3.connect(DB); c = conn.cursor(); db_init(c)
    repos = {}
    errors = 0
    for q in cfg["queries"]:
        query = quote(f'{q["query"]} stars:>={limits.get("min_stars",100)}')
        try:
            data = gh(f"/search/repositories?q={query}&sort=stars&order=desc&per_page={limits.get('per_query',20)}")
            for r in data.get("items", []):
                repos[r["id"]] = (r, q["category"])
        except Exception as e:
            errors += 1
            print("discovery error", q["name"], e)
        time.sleep(.15)
    repos = list(repos.values())[:limits.get("max_repositories",250)]
    now = datetime.now(timezone.utc).isoformat()
    rows=[]
    for r, category in repos:
        lic = (r.get("license") or {}).get("spdx_id")
        c.execute("SELECT id FROM repositories WHERE id=?", (r["id"],)); old=c.fetchone()
        c.execute("INSERT OR REPLACE INTO repositories(id,full_name,name,url,description,language,license,topics,category,discovered_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
          (r["id"],r["full_name"],r["name"],r["html_url"],r.get("description"),r.get("language"),lic,json.dumps(r.get("topics",[])),category,old and None or now,now))
        c.execute("SELECT stars FROM snapshots WHERE repo_id=? ORDER BY id DESC LIMIT 1", (r["id"],)); prev=c.fetchone()
        growth = 50 if not prev else max(0,min(100,50+(r["stargazers_count"]-prev[0])*100/max(prev[0],1)))
        lscore = {"MIT":100,"Apache-2.0":95,"BSD-2-Clause":95,"BSD-3-Clause":95,"ISC":95,"MPL-2.0":75,"LGPL-3.0":65,"LGPL-2.1":65,"GPL-3.0":55,"GPL-2.0":55,"AGPL-3.0":45,"SSPL-1.0":20,"BSL-1.1":25,None:10}.get(lic,40)
        total,conf,_,market,saas,ai,loc,best,fast,long=score(r,category,lscore)
        c.execute("INSERT INTO snapshots(repo_id,scanned_at,stars,forks,watchers,open_issues,subscribers,pushed_at,updated_at,default_branch,size_kb) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
          (r["id"],now,r["stargazers_count"],r["forks_count"],r["watchers_count"],r["open_issues_count"],r.get("subscribers_count",0),r.get("pushed_at"),r.get("updated_at"),r.get("default_branch"),r.get("size",0)))
        c.execute("INSERT OR REPLACE INTO opportunities(repo_id,scanned_at,score,confidence,growth_score,license_score,market_score,saas_score,ai_score,localization_score,best_path,fastest_path,long_term_path,rationale) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (r["id"],now,total,conf,growth,lscore,market,saas,ai,loc,best,fast,long,"Deterministic score from GitHub metadata; business recommendations are hypotheses, not revenue guarantees."))
        rows.append((total,r,growth,lic,best,fast,long))
    conn.commit()
    rows.sort(key=lambda x:x[0], reverse=True)
    REPORTS.mkdir(exist_ok=True)
    lines=["# Open Source Opportunity Radar — Daily Report","",f"Generated: {now}","",f"Repositories scanned: {len(rows)}","", "## Top Opportunities",""]
    for i,(s,r,g,lic,best,fast,long) in enumerate(rows[:50],1):
        lines += [f"### {i}. [{r['full_name']}]({r['html_url']}) — {s}/100",f"- Category: {r.get('description') or 'N/A'}",f"- Stars: {r['stargazers_count']:,} | Forks: {r['forks_count']:,} | Growth signal: {g:.1f}",f"- License: {lic or 'Unknown'}",f"- Best path: **{best}**",f"- Fastest path: **{fast}**",f"- Long term: **{long}**",""]
    (REPORTS/"latest.md").write_text("\n".join(lines),encoding="utf-8")
    (ROOT/"data"/"latest.json").write_text(json.dumps({"generated_at":now,"count":len(rows),"top":[{"full_name":r["full_name"],"url":r["html_url"],"score":s,"stars":r["stargazers_count"],"license":lic,"best_path":best} for s,r,g,lic,best,fast,long in rows[:100]]},ensure_ascii=False,indent=2),encoding="utf-8")
    finished=datetime.now(timezone.utc).isoformat(); c.execute("INSERT INTO scan_runs(started_at,finished_at,repos_found,errors) VALUES(?,?,?,?)",(started,finished,len(rows),errors)); conn.commit(); conn.close()
    print(f"scan complete: {len(rows)} repositories, {errors} errors")

if __name__ == "__main__": main()
