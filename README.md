# fließband.

**A data pipeline that monitors itself.**

Fließband (German: *assembly line*) ingests German energy and weather data
every day, checks its own work, and publishes its health — run history,
data-quality checks and a freshness SLO — on a public status page.

**Live:** [fliessband.vivekreddy.de](https://fliessband.vivekreddy.de) ·
a project by [Vivekananda Reddy](https://vivekreddy.de)

## Architecture

```
GitHub Actions (cron, 05:30 UTC)
  └─ python -m pipeline.ingest
       ├─ Energy-Charts API  → daily generation mix, load, prices
       ├─ Bright Sky (DWD)   → daily weather for Berlin/Hamburg/München
       ├─ data-quality checks (plausibility, freshness SLO)
       ├─ idempotent upserts → data/fliessband.db  (SQLite, committed)
       └─ JSON snapshots     → public/data/*.json
  └─ commit + push  →  Vercel redeploys the status page
```

**Why SQLite in git ("baked data")?** For a dataset of ~10 rows/day, a
database server is overhead without benefit. Committing the database makes
every pipeline run a public, diffable, revertible artifact — the git log
*is* the ops log, and the Actions history *is* the uptime record. Anyone
can audit exactly what changed and when.

## The ops story

- **Idempotent** — every row is an upsert keyed by date; any range can be
  re-run safely. The daily job re-ingests two days so late upstream
  corrections heal automatically.
- **Self-checking** — plausibility checks on every row (generation totals,
  price ranges, sensor sanity) plus a freshness SLO: yesterday's data must
  be present, or the run is marked degraded.
- **Honest failure modes** — runs report `ok / degraded / failed`; a
  hard-failed run exits non-zero and shows red in the Actions history.
  Upstream rate limits leave visible gaps, not silently interpolated data.
- **Tested** — transform and check logic covered by pytest, run in CI on
  every push.

## Run it

```bash
pip install -r requirements.txt
python -m pipeline.ingest --backfill 365   # first fill (~3 min)
npm install && npm run dev                 # status page on :3000
python -m pytest tests/ -q                 # tests
```

No API keys, no env vars, no database server.

## Data & attribution

- Energy: [Energy-Charts API](https://api.energy-charts.info) by
  **Fraunhofer ISE**; price data **CC BY 4.0 Bundesnetzagentur | SMARD.de**
- Weather: [Bright Sky](https://brightsky.dev), serving **DWD**
  (Deutscher Wetterdienst) open data

## Provenance

This repository previously held "SalesLytic" — SQL/Tableau/Power BI course
exercises from my data-analytics learning phase (preserved in git history).
Fließband is original work: a from-scratch rebuild of the same interest —
data and what it can tell you — at engineering depth.
