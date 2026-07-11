"""Exports the SQLite contents to JSON snapshots consumed by the status
site (public/data/*.json). Baked data: the site never queries a database.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

PUBLIC_DATA = Path(__file__).resolve().parent.parent / "public" / "data"


def _rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def export_all(conn: sqlite3.Connection) -> None:
    PUBLIC_DATA.mkdir(parents=True, exist_ok=True)

    energy = _rows(
        conn,
        """SELECT * FROM (
             SELECT * FROM energy_daily ORDER BY date DESC LIMIT 400
           ) ORDER BY date ASC""",
    )
    weather = _rows(
        conn,
        """SELECT * FROM (
             SELECT * FROM weather_daily ORDER BY date DESC LIMIT 1300
           ) ORDER BY date ASC, city ASC""",
    )
    runs = _rows(conn, "SELECT * FROM runs ORDER BY id DESC LIMIT 40")

    # Wind speed (Berlin/Hamburg/München avg) vs wind generation, per day —
    # the pipeline's showcase join.
    wind_join = _rows(
        conn,
        """SELECT e.date,
                  ROUND(AVG(w.wind_speed_avg), 1) AS wind_speed_avg,
                  e.wind_onshore_mw + e.wind_offshore_mw AS wind_mw
           FROM energy_daily e
           JOIN weather_daily w ON w.date = e.date
           WHERE w.wind_speed_avg IS NOT NULL
           GROUP BY e.date ORDER BY e.date ASC""",
    )

    latest_energy = energy[-1] if energy else None
    now = datetime.now(timezone.utc)
    freshness_hours = None
    if latest_energy:
        latest_day = datetime.fromisoformat(latest_energy["date"]).replace(
            tzinfo=timezone.utc
        )
        freshness_hours = round((now - latest_day).total_seconds() / 3600, 1)

    status = {
        "generatedAt": now.isoformat(),
        "sloHours": 50,  # data for day N must land by end of day N+1
        "freshnessHours": freshness_hours,
        "freshnessOk": freshness_hours is not None and freshness_hours <= 50,
        "latestDataDate": latest_energy["date"] if latest_energy else None,
        "totals": {
            "energyDays": conn.execute(
                "SELECT COUNT(*) AS n FROM energy_daily"
            ).fetchone()["n"],
            "weatherRows": conn.execute(
                "SELECT COUNT(*) AS n FROM weather_daily"
            ).fetchone()["n"],
            "runs": conn.execute("SELECT COUNT(*) AS n FROM runs").fetchone()["n"],
        },
        "runs": runs,
    }

    for name, payload in [
        ("status", status),
        ("energy", energy),
        ("weather", weather),
        ("wind_join", wind_join),
    ]:
        (PUBLIC_DATA / f"{name}.json").write_text(
            json.dumps(payload, separators=(",", ":"))
        )
