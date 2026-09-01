# Product Specification

## 1. Discovery

Discover repositories across configurable categories rather than searching all of GitHub literally.

Initial categories:

- AI Agents
- LLM / RAG
- AI Coding
- Generative Image / Video / Audio
- E-commerce
- CRM / ERP / POS
- CMS / No-code / Low-code
- DevOps / Cloud
- Databases / Data
- Analytics / BI
- Documents / PDF / OCR
- Education
- Finance
- IoT
- GPS / Fleet
- Smart Home
- Games / Game Engines
- Productivity
- Media
- Security tooling where commercial use is legitimate

Discovery should prioritize:

- high-quality repositories
- active maintenance
- meaningful star growth
- releases
- contributor growth
- ecosystem activity
- commercial relevance

## 2. Repository Snapshot

Persist at least:

- owner
- name
- URL
- description
- topics
- primary language
- license SPDX if available
- stars
- forks
- open issues
- watchers where available
- contributors where available
- created_at
- updated_at
- pushed_at
- latest release
- default branch
- archived status
- snapshot timestamp

Never overwrite historical snapshots.

## 3. Change Detection

Compare every new snapshot against the latest previous snapshot.

Calculate:

- star delta
- star growth percentage
- fork delta
- contributor delta when available
- release delta
- issue activity
- repository activity
- license change
- description/topic change

Create events such as:

- NEW_PROJECT
- RISING_PROJECT
- MAJOR_RELEASE
- LICENSE_CHANGE
- COMMUNITY_GROWTH
- ACTIVITY_SURGE
- COMMERCIAL_SIGNAL

## 4. Business Analysis

For each high-value repository determine:

- what it does
- problem solved
- target users
- target paying customers
- strengths
- weaknesses
- missing features
- market gap
- competitors
- localization opportunity
- AI opportunity
- SaaS opportunity
- Enterprise opportunity
- API opportunity
- Plugin/Extension opportunity
- Hosting/Managed Service opportunity
- Installation/Customization/Support opportunity
- White-label opportunity only when license permits

## 5. Revenue Scoring

Produce separate scores from 0 to 100:

- Technical Quality
- Growth
- Community
- Market Potential
- Commercial Freedom
- SaaS Potential
- AI Opportunity
- Localization Opportunity
- Time-to-Money
- Revenue Potential
- Overall Opportunity

Every score must include an explanation and confidence level.

Do not present speculative revenue as guaranteed income.

## 6. License Intelligence

License analysis must inspect repository license metadata and, where practical, LICENSE/NOTICE files and relevant project documentation.

Classify:

- Commercial Friendly
- Copyleft / Compliance Required
- Network Copyleft / Compliance Required
- Source-Available / Restrictions
- Custom / Manual Review
- Unknown

Never claim that a project can be resold, relicensed, white-labeled or converted into SaaS solely from its popularity.

## 7. Product Ideas

For promising repositories generate at least 5 product ideas.

Each idea contains:

- name
- customer
- problem
- proposed product
- differentiator
- monetization model
- implementation difficulty
- time-to-first-revenue estimate
- recurring revenue potential
- license risk
- confidence

## 8. Persian / Localization Analysis

Evaluate independently:

- Persian translation
- RTL
- Jalali calendar
- Persian search
- local currency formatting
- local payment integrations
- SMS integrations
- local accounting/business workflows

Localization alone is not considered sufficient differentiation unless there is evidence of market value.

## 9. Reports

Generate:

- Daily Changes
- New Projects
- Rising Projects
- Top Business Opportunities
- Top AI Opportunities
- Top SaaS Opportunities
- Top Localization Opportunities
- Fastest-to-Money Opportunities
- Low-Cost Opportunities
- Enterprise Opportunities
- License Changes
- Weekly Business Report
- Monthly Ranking

## 10. User Workflow

The user should be able to answer in seconds:

1. What is new?
2. What is growing unusually fast?
3. What changed since my last check?
4. Which projects have commercial potential?
5. How can I make money from each one?
6. Which opportunity should I investigate first?

## 11. LLM Usage

LLMs are used for semantic analysis, product ideation, business reasoning and report generation.

Deterministic GitHub metrics must be calculated by code, not invented by an LLM.

Provider abstraction should support OpenAI-compatible APIs and configurable providers such as OpenRouter and local models.

## 12. Automation

GitHub Actions should support:

- daily fast scan
- weekly deep scan
- monthly full ranking
- report generation
- artifact publication

All jobs must be idempotent and safe to rerun.
