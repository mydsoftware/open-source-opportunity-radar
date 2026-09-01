# Operations

## Secrets

Optional:

- `LLM_API_KEY`: API key for an OpenAI-compatible LLM endpoint.
- `LLM_BASE_URL`: endpoint base, default `https://openrouter.ai/api/v1`.
- `LLM_MODEL`: model name, default `openai/gpt-oss-20b:free`.

`GITHUB_TOKEN` is supplied automatically by GitHub Actions.

## Cadence

- Daily: discovery + snapshots + ranking + dashboard.
- Weekly: deep semantic business analysis.
- Monthly: full ranking refresh.

## Outputs

- `data/radar.sqlite3`: historical database.
- `data/latest.json`: machine-readable ranking.
- `data/business-cases/`: LLM business cases when configured.
- `reports/latest.md`: human-readable report.
- `dashboard/index.html`: static dashboard.

## Local

```bash
pip install -r requirements.txt
GITHUB_TOKEN=... python scripts/scan.py
LLM_API_KEY=... python scripts/llm_analyze.py
python scripts/build_dashboard.py
python -m pytest -q
```
