"""Fließband ingest job.

Usage:
  python -m pipeline.ingest                # daily mode: yesterday + day before
  python -m pipeline.ingest --backfill 365 # initial history load

Idempotent: every row is an upsert keyed by date (+city), so re-running
any range is safe. Exits non-zero when the run fails outright, so the
GitHub Actions history doubles as an uptime log.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date, datetime, timedelta, timezone

from . import checks as quality
from .db import connect, record_run, upsert_energy, upsert_weather
from .export import export_all
from .sources import CITIES, fetch_energy_range, fetch_weather_range

CHUNK_DAYS = 30


def run(mode: str, start: date, end: date) -> int:
    started_at = datetime.now(timezone.utc).isoformat()
    conn = connect()

    rows_energy = rows_weather = 0
    failed_checks: list[str] = []
    passed_checks = 0
    notes: list[str] = []
    hard_failure = False

    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=CHUNK_DAYS - 1), end)
        window = f"{cursor} → {chunk_end}"

        try:
            energy_rows = fetch_energy_range(cursor, chunk_end)
            for row in energy_rows.values():
                for name, ok, detail in quality.check_energy_row(row):
                    if ok:
                        passed_checks += 1
                    else:
                        failed_checks.append(f"{name} ({detail})")
                upsert_energy(conn, row)
                rows_energy += 1
        except Exception as error:  # noqa: BLE001
            hard_failure = True
            notes.append(f"energy {window}: {error}")

        for city in CITIES:
            try:
                weather_rows = fetch_weather_range(cursor, chunk_end, city)
                for row in weather_rows.values():
                    for name, ok, detail in quality.check_weather_row(row):
                        if ok:
                            passed_checks += 1
                        else:
                            failed_checks.append(f"{name} ({detail})")
                    upsert_weather(conn, row)
                    rows_weather += 1
            except Exception as error:  # noqa: BLE001
                hard_failure = True
                notes.append(f"weather/{city} {window}: {error}")
            time.sleep(0.3)  # be polite to Bright Sky

        conn.commit()
        cursor = chunk_end + timedelta(days=1)
        if cursor <= end:
            time.sleep(2.0)  # pace chunked backfills below rate limits

    for name, ok, detail in quality.check_freshness(conn):
        if ok:
            passed_checks += 1
        else:
            failed_checks.append(f"{name} ({detail})")

    status = "failed" if hard_failure and rows_energy == 0 else (
        "degraded" if hard_failure or failed_checks else "ok"
    )

    record_run(conn, {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "dates_processed": (end - start).days + 1,
        "rows_energy": rows_energy,
        "rows_weather": rows_weather,
        "checks_passed": passed_checks,
        "checks_failed": len(failed_checks),
        "status": status,
        "notes": "; ".join(notes + failed_checks[:5])[:900],
    })
    conn.commit()

    export_all(conn)
    conn.close()

    print(
        f"[fliessband] {mode} {start}→{end}: {status} | "
        f"energy={rows_energy} weather={rows_weather} "
        f"checks {passed_checks} passed / {len(failed_checks)} failed"
    )
    for note in notes:
        print(f"  ! {note}", file=sys.stderr)

    return 1 if status == "failed" else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Fließband ingest")
    parser.add_argument("--backfill", type=int, metavar="DAYS")
    args = parser.parse_args()

    today = date.today()
    if args.backfill:
        start, end, mode = today - timedelta(days=args.backfill), today - timedelta(days=1), "backfill"
    else:
        # Re-ingest two days: yesterday plus the day before, so late
        # upstream corrections are picked up automatically.
        start, end, mode = today - timedelta(days=2), today - timedelta(days=1), "daily"

    sys.exit(run(mode, start, end))


if __name__ == "__main__":
    main()
