import type { AgentDefinition } from './types/agent-definition'

const outputSchema = {
  type: 'object' as const,
  properties: {
    what_it_does: { type: 'string' as const },
    problem_solved: { type: 'string' as const },
    why_it_matters: { type: 'string' as const },
    best_products: {
      type: 'array' as const,
      items: {
        type: 'object' as const,
        properties: {
          product: { type: 'string' as const },
          customer: { type: 'string' as const },
          example_usage: { type: 'string' as const },
          sales_pitch: { type: 'string' as const },
          monetization: { type: 'string' as const },
          pricing: { type: 'string' as const },
          localization: { type: 'string' as const },
          difficulty: { type: 'string' as const },
          time_to_money: { type: 'string' as const },
          license_risk: { type: 'string' as const },
        },
        required: ['product','customer','example_usage','sales_pitch','monetization','pricing','localization','difficulty','time_to_money','license_risk'],
      },
    },
    recommendation: { type: 'string' as const },
  },
  required: ['what_it_does','problem_solved','why_it_matters','best_products','recommendation'],
}

const definition: AgentDefinition = {
  id: 'open-source-opportunity-analyst',
  displayName: 'Open Source Opportunity Analyst',
  model: 'deepseek/deepseek-v4-flash',
  reasoningOptions: { enabled: true, effort: 'medium' },
  providerOptions: { sort: 'price', max_price: { prompt: 0, completion: 0 } },
  toolNames: ['read_files', 'find_files', 'code_search', 'web_search', 'read_docs', 'read_url', 'set_output'],
  outputMode: 'structured_output',
  outputSchema,
  spawnerPrompt: 'Use this agent to deeply analyze one open-source repository for practical product and revenue opportunities. It must inspect the actual repository before making recommendations.',
  instructionsPrompt: `تو تحلیلگر ارشد Open Source، Product و Business هستی.

مأموریت: فقط یک Repository را بررسی کن و برای همان Repository یک تحلیل تجاری کاملاً اختصاصی تولید کن.

قوانین سخت:
1. ابتدا README، ساختار فایل‌ها، package/pyproject/go.mod یا فایل‌های اصلی، LICENSE، Topics و در صورت امکان Issues/README آنلاین را بررسی کن.
2. توضیح GitHub را هرگز به‌عنوان تحلیل نهایی کپی نکن.
3. برای پروژه‌های مختلف از جمله‌های قالبی یکسان استفاده نکن.
4. دقیقاً بگو این پروژه چه قابلیت فنی منحصربه‌فردی دارد و چه مشکلی را حل می‌کند.
5. حداقل 2 و حداکثر 3 محصول مشخص و متفاوت پیشنهاد بده؛ نه «یک SaaS عمومی».
6. برای هر محصول یک مشتری مشخص، سناریوی واقعی استفاده، متن فروش به مشتری و روش قیمت‌گذاری بده.
7. بازار فارسی/ایران را در نظر بگیر، اما درآمد را تضمین نکن.
8. اگر پروژه برای درآمد مستقیم مناسب نیست، صریح بگو و بهترین مدل خدماتی/ابزاری جایگزین را ارائه کن.
9. License را از روی فایل واقعی بررسی کن و ریسک را دقیق توضیح بده.
10. تمام خروجی فارسی باشد، به‌جز نام‌های فنی و برندها.
11. از عبارات کلی مانند «قابلیت اصلی پروژه را در یک پنل فارسی قرار بده» استفاده نکن مگر اینکه واقعاً بهترین پیشنهاد برای همان پروژه باشد.
12. اگر برای ادعایی داده کافی نداری، آن را حدس نزن؛ محدودیت را ذکر کن.

خروجی فقط مطابق JSON Schema باشد.`,
}

export default definition
