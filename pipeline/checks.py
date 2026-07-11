"""Data-quality checks. Each returns (name, passed, detail) — the run is
marked degraded when any check fails, and the status page shows why.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

Check = tuple[str, bool, str]


def check_energy_row(row: dict) -> list[Check]:
    checks: list[Check] = []
    total = row.get("total_mw") or 0
    checks.append((
        f"energy[{row['date']}] total generation plausible",
        20_000 <= total <= 120_000,
        f"total_mw={total}",
    ))
    share = row.get("ren_share_pct")
    checks.append((
        f"energy[{row['date']}] renewable share in range",
        share is None or 0 <= share <= 150,
        f"ren_share_pct={share}",
    ))
    price = row.get("price_avg")
    checks.append((
        f"energy[{row['date']}] price plausible",
        price is None or -500 <= price <= 3000,
        f"price_avg={price}",
    ))
    return checks


def check_weather_row(row: dict) -> list[Check]:
    temp = row.get("temp_avg")
    return [(
        f"weather[{row['date']}/{row['city']}] temperature plausible",
        temp is None or -35 <= temp <= 45,
        f"temp_avg={temp}",
    )]


def check_freshness(conn: sqlite3.Connection) -> list[Check]:
    """The pipeline's headline SLO: yesterday's energy data must exist."""
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM energy_daily WHERE date >= ?", (yesterday,)
    ).fetchone()
    return [(
        "freshness: energy data for yesterday present",
        row["n"] > 0,
        f"rows_since_{yesterday}={row['n']}",
    )]
