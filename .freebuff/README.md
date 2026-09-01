# Freebuff integration — Open Source Opportunity Radar

این پوشه قرارداد اجرای تحلیل با Freebuff است.

## روش اجرا

1. Repository را در Freebuff باز کن.
2. Agent زیر را انتخاب/فعال کن:
   `.agents/open-source-opportunity-analyst.ts`
3. فایل صف را باز کن:
   `data/freebuff-queue/queue.json`
4. برای هر رکورد، Repository معرفی‌شده را عمیقاً بررسی کن.
5. خروجی را دقیقاً در مسیر زیر ذخیره کن:
   `data/business-cases/<owner>__<repo>.json`
6. بعد از اتمام، `python scripts/import_freebuff_results.py` را اجرا کن.
7. سپس `python scripts/build_dashboard.py` را اجرا کن.

## قانون مهم

هر Repository باید تحلیل اختصاصی خودش را داشته باشد. تغییر نام پروژه در یک Template قابل قبول نیست.
README، ساختار فایل‌ها، LICENSE، Topics و قابلیت‌های واقعی Repository باید بررسی شوند.

خروجی باید JSON مطابق Schema Agent باشد.
