#!/usr/bin/env python3
"""Optional semantic business analysis through any OpenAI-compatible endpoint."""
import json, os
from pathlib import Path
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]
API=os.getenv('LLM_BASE_URL','https://openrouter.ai/api/v1').rstrip('/')+'/chat/completions'
KEY=os.getenv('LLM_API_KEY','')
MODEL=os.getenv('LLM_MODEL','openai/gpt-oss-20b:free')

PROMPT='''You are an open-source business analyst. Analyze this GitHub repository using only the supplied facts. Return strict JSON with: what_it_does, target_users, paying_customers, missing_features, business_opportunities (array of objects with product, customer, monetization, difficulty, time_to_money, license_risk), best_path, fastest_path, long_term_path, confidence, evidence. Never guarantee revenue. Distinguish facts from hypotheses.'''

def main():
    if not KEY:
        print('LLM_API_KEY not configured; semantic analysis skipped')
        return
    data=json.loads((ROOT/'data/latest.json').read_text(encoding='utf-8'))
    out=ROOT/'data'/'business-cases'; out.mkdir(parents=True,exist_ok=True)
    for item in data.get('top',[])[:25]:
        payload={'model':MODEL,'temperature':0.1,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':PROMPT},{'role':'user','content':json.dumps(item,ensure_ascii=False)}]}
        req=Request(API,data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=90) as r: result=json.loads(r.read().decode())
            content=result['choices'][0]['message']['content']
            (out/(item['full_name'].replace('/','__')+'.json')).write_text(content,encoding='utf-8')
        except Exception as e: print('LLM analysis failed',item['full_name'],e)

if __name__=='__main__': main()
