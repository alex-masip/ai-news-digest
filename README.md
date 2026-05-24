# ai-news-digest

Personal daily AI news digest. Pulls English-language AI articles from
[GDELT GAL](https://blog.gdeltproject.org/gdelt-global-article-list-gal/) on
BigQuery, filters/dedups/ranks, drops a Claude-generated 3-sentence intro on top,
and renders a static HTML page deployed to Vercel.

Runs daily at 06:00 UTC (~07:00 / 08:00 Madrid) via GitHub Actions.

## GAL coverage caveat

GDELT GAL ingests open-press URLs reliably but barely captures paywalled
outlets — Reuters, Bloomberg, FT, WSJ, AP typically return zero rows per day.
Tier-1 coverage in the digest is dominated by NYT, The Verge, TechCrunch,
Wired, Engadget, Ars Technica. Long-tail clusters with high outlet counts
(60-70x) are often wire-syndication networks rather than independent coverage.

## Layout

- `src/` — fetch, filter, dedup, summarize, render, run
- `config/` — outlet whitelist + blocklist + AI keyword regex
- `templates/` — Jinja HTML template
- `public/` — Vercel output (one HTML per day + `index.html` copy of latest)
- `data/` — JSON archive of each day's curated set

## Local run

```fish
python -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
set -gx GOOGLE_APPLICATION_CREDENTIALS /path/to/sa.json
set -gx ANTHROPIC_API_KEY sk-ant-...
python -m src.run                # Madrid-yesterday
python -m src.run --date 2026-05-20   # backfill a specific Madrid day
```
