#!/usr/bin/env python3
"""تحلیل اختصاصی فرصت کسب‌وکار برای هر Repository؛ LLM در صورت وجود کلید، fallback اختصاصی در غیر این صورت."""
import json, os
from pathlib import Path
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]
API=os.getenv('LLM_BASE_URL','https://openrouter.ai/api/v1').rstrip('/')+'/chat/completions'
KEY=os.getenv('LLM_API_KEY','')
MODEL=os.getenv('LLM_MODEL','openai/gpt-oss-20b:free')
OUT=ROOT/'data'/'business-cases'
PROMPT='''تو یک تحلیلگر ارشد Open Source و Product/Business هستی. Repository زیر را فقط بر اساس اطلاعات داده‌شده تحلیل کن. خروجی فقط JSON معتبر و تمام متن‌ها فارسی باشد. تحلیل باید کاملاً اختصاصی همین Repository باشد و نام، قابلیت، حوزه، زبان و موضوعات واقعی آن را در متن استفاده کند. برای دو Repository متفاوت متن یکسان تولید نکن. JSON شامل what_it_does, why_it_matters, best_path, business_opportunities, missing_features, paying_customers, fastest_path, long_term_path, confidence, license_notes باشد. business_opportunities حداکثر 3 مورد و هر مورد شامل product, customer, monetization, example_usage, sales_pitch, localization, difficulty, time_to_money, license_risk باشد. هیچ درآمدی را تضمین نکن.'''

def fallback(item):
    n=item.get('full_name','پروژه'); d=item.get('description') or 'توضیح کافی در GitHub ثبت نشده است.'; cat=item.get('category') or 'سایر'; lang=item.get('language') or 'نامشخص'; topics=item.get('topics') or []; t='، '.join(topics[:5]) or cat
    product=f'سرویس تخصصی «{n}» برای استفاده غیر فنی از قابلیت اصلی همین Repository، با پنل فارسی و اتصال به نیازهای بازار {cat}.'
    customer=f'تیم‌ها و کسب‌وکارهایی که برای قابلیت «{n}» در حوزه {cat} کاربرد عملی دارند، به‌خصوص کاربران فنی {lang}.'
    return {'what_it_does':f'پروژه «{n}» در GitHub این توضیح را دارد: {d} موضوعات مرتبط: {t}. زبان اصلی: {lang}.','why_it_matters':f'ارزش اصلی «{n}» این است که قابلیت فعلی آن می‌تواند به‌جای استفاده مستقیم توسط توسعه‌دهنده، به یک راه‌حل آماده برای حوزه {cat} تبدیل شود.','best_path':product,'business_opportunities':[{'product':product,'customer':customer,'monetization':'هزینه راه‌اندازی + اشتراک + سفارشی‌سازی و پشتیبانی.','example_usage':f'مشتری «{customer}» از پنل فارسی استفاده می‌کند تا قابلیت اصلی «{n}» را بدون درگیری با کد و تنظیمات پیچیده اجرا کند.','sales_pitch':f'«ما {n} را متناسب با نیاز {cat} شما آماده می‌کنیم؛ فارسی‌سازی، نصب، اتصال و پشتیبانی را هم انجام می‌دهیم.»','localization':'رابط فارسی و RTL، آموزش فارسی، پنل ساده، اتصال به سرویس‌های موردنیاز بازار هدف.','difficulty':'متوسط','time_to_money':'حدود ۱ تا ۴ هفته برای MVP خدماتی؛ وابسته به پیچیدگی پروژه.','license_risk':f'مجوز ثبت‌شده: {item.get("license") or "نامشخص"؛ قبل از استفاده تجاری بررسی شود.'}}],'missing_features':['رابط فارسی و RTL','پنل کاربر غیر فنی','مستندات و آموزش فارسی','اتصال به سرویس‌های بازار هدف'],'paying_customers':customer,'fastest_path':f'یک نمونه کوچک مبتنی بر قابلیت واقعی «{n}» برای یک مشتری حوزه {cat} بساز و ابتدا هزینه راه‌اندازی و سفارشی‌سازی بگیر.','long_term_path':f'پس از اثبات تقاضا، قابلیت «{n}» را به SaaS تخصصی حوزه {cat} تبدیل کن و امکانات مدیریت، گزارش، اتصال و پشتیبانی را به مزیت محصول تبدیل کن.','confidence':60,'license_notes':f'لایسنس فعلی: {item.get("license") or "نامشخص"}. قبل از فروش، LICENSE و NOTICE و وابستگی‌ها بررسی شوند.'}

def main():
    data=json.loads((ROOT/'data/latest.json').read_text(encoding='utf-8')); OUT.mkdir(parents=True,exist_ok=True)
    for item in data.get('top',[])[:100]:
        result=None
        if KEY:
            user={k:item.get(k) for k in ('full_name','description','url','language','topics','stars','license','category','score')}
            payload={'model':MODEL,'temperature':0.15,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':PROMPT},{'role':'user','content':json.dumps(user,ensure_ascii=False)}]}
            try:
                req=Request(API,data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
                with urlopen(req,timeout=90) as r: result=json.loads(json.loads(r.read().decode())['choices'][0]['message']['content'])
            except Exception as e: print('LLM analysis failed',item['full_name'],e)
        if not isinstance(result,dict) or not result.get('what_it_does') or not result.get('business_opportunities'):
            result=fallback(item); result['_source']='repository_specific_fallback'
        (OUT/(item['full_name'].replace('/','__')+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'business analysis complete: {min(len(data.get("top",[])),100)} repositories')
if __name__=='__main__': main()
