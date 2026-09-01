# Open Source Opportunity Radar

Open Source Opportunity Radar یک سیستم دائمی برای کشف، پایش و تحلیل پروژه‌های Open Source و تبدیل تغییرات GitHub به فرصت‌های قابل درآمدزایی است.

## هدف

این پروژه هر بار که اجرا می‌شود:

1. پروژه‌های مهم Open Source را کشف می‌کند.
2. پروژه‌های جدید و پروژه‌های در حال رشد را تشخیص می‌دهد.
3. وضعیت Repository، Release، Stars، Forks، Contributors و License را Snapshot می‌کند.
4. تغییرات نسبت به اسکن قبلی را محاسبه می‌کند.
5. کاربرد واقعی پروژه را تحلیل می‌کند.
6. فرصت‌های تجاری، SaaS، Enterprise، Plugin، API، Hosting، Services و Localization را استخراج می‌کند.
7. ریسک License را بررسی می‌کند.
8. برای هر پروژه Business Score و Revenue Score تولید می‌کند.
9. گزارش روزانه/هفتگی قابل خواندن تولید می‌کند.

## اصل مهم

این پروژه صرفاً «لیست پروژه‌های محبوب GitHub» نیست. هدف آن پاسخ به این سؤال است:

> از تغییرات جدید Open Source چه محصول یا خدمتی می‌توان ساخت و سریع‌ترین و بهترین مسیر درآمدزایی چیست؟

## معماری

```text
GitHub Search/API
      ↓
Discovery
      ↓
Repository Snapshots
      ↓
Growth & Change Detection
      ↓
Technical Analysis
      ↓
License Intelligence
      ↓
Business Analysis
      ↓
Opportunity Scoring
      ↓
Reports / Dashboard / Alerts
```

## اجرای دوره‌ای

- Fast scan: روزانه
- Deep analysis: هفتگی
- Full re-ranking: ماهانه

## وضعیت

Repository initialized. Implementation is being built incrementally with an automation-first architecture.

## License

MIT
