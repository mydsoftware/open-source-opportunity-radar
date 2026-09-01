#!/usr/bin/env python3
"""تحلیل اختصاصی فرصت کسب‌وکار برای هر Repository با endpoint سازگار با OpenAI."""
import json, os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
API=os.getenv('LLM_BASE_URL','https://openrouter.ai/api/v1').rstrip('/')+'/chat/completions'
KEY=os.getenv('LLM_API_KEY','')
MODEL=os.getenv('LLM_MODEL','openai/gpt-oss-20b:free')

PROMPT='''تو یک تحلیلگر ارشد Open Source و Product/Business هستی. Repository زیر را فقط بر اساس اطلاعات داده‌شده تحلیل کن.
خروجی فقط JSON معتبر باشد و تمام مقادیر توضیحی حتماً فارسی، ساده، دقیق و قابل فهم برای صاحب کسب‌وکار باشند.
برای هر Repository تحلیل باید کاملاً اختصاصی باشد و از جملات عمومی و قابل کپی برای پروژه‌های دیگر استفاده نکن.
نام و قابلیت واقعی همین Repository را در متن بیاور و توضیح بده دقیقاً چه مسئله‌ای را حل می‌کند.
اگر اطلاعات کافی نیست، صادقانه بگو «اطلاعات کافی نیست» و حدس را با برچسب فرضیه مشخص کن.
هیچ درآمدی را تضمین نکن.

JSON دقیقاً این فیلدها را داشته باشد:
what_it_does: کاربرد واقعی همین پروژه، فارسی و اختصاصی
why_it_matters: چرا این پروژه برای بازار می‌تواند ارزشمند باشد
best_path: بهترین محصول/سرویس مشخصی که می‌توان با همین پروژه ساخت، اختصاصی برای همین پروژه
business_opportunities: آرایه حداکثر 3 فرصت، هرکدام شامل:
  product: نام و شرح یک محصول مشخص و متفاوت برای همین پروژه
  customer: مشتری مشخص
  monetization: مدل درآمدی مشخص
  example_usage: یک مثال واقعی از نحوه استفاده محصول توسط مشتری
  sales_pitch: یک مثال کوتاه از اینکه چطور همان محصول را به مشتری بفروشیم
  localization: قابلیت‌های فارسی‌سازی/بومی‌سازی لازم
  difficulty: ساده/متوسط/سخت
  time_to_money: برآورد تقریبی و محتاطانه زمان رسیدن به اولین درآمد
  license_risk: توضیح ریسک لایسنس
missing_features: آرایه قابلیت‌هایی که برای محصول پیشنهادی کم است
paying_customers: مشتریانی که احتمالاً حاضرند پول بدهند
fastest_path: سریع‌ترین مسیر عملی و قانونی برای رسیدن به اولین درآمد
long_term_path: مسیر تبدیل نمونه اولیه به کسب‌وکار پایدار
confidence: عدد 0 تا 100
license_notes: نکات مهم لایسنس

مهم: «کاربرد برای شما»، مثال استفاده و مثال فروش باید از قابلیت واقعی همین Repository استخراج شوند؛ برای دو Repository متفاوت نباید متن یکسان تولید کنی.'''

def main():
    if not KEY:
        print('LLM_API_KEY not configured; semantic analysis skipped')
        return
    data=json.loads((ROOT/'data/latest.json').read_text(encoding='utf-8'))
    out=ROOT/'data'/'business-cases'; out.mkdir(parents=True,exist_ok=True)
    for item in data.get('top',[])[:25]:
        user={k:item.get(k) for k in ('full_name','description','url','language','topics','stars','license','category','score')}
        payload={'model':MODEL,'temperature':0.2,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':PROMPT},{'role':'user','content':json.dumps(user,ensure_ascii=False)}]}
        req=Request(API,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
        try:
            with urlopen(req,timeout=90) as r: result=json.loads(r.read().decode())
            content=result['choices'][0]['message']['content']
            parsed=json.loads(content)
            (out/(item['full_name'].replace('/','__')+'.json')).write_text(json.dumps(parsed,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as e:
            print('LLM analysis failed',item['full_name'],e)

if __name__=='__main__': main()
