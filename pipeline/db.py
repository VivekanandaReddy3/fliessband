"""SQLite storage for Fließband. The database file is committed to the
repo — the pipeline's full history is auditable in git (baked-data
pattern). Rows are keyed by date and upserted, so re-runs are idempotent.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "fliessband.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS energy_daily (
    date TEXT PRIMARY KEY,           -- YYYY-MM-DD (Europe/Berlin)
    solar_mw REAL, wind_onshore_mw REAL, wind_offshore_mw REAL,
    hydro_mw REAL, biomass_mw REAL, gas_mw REAL, coal_mw REAL, other_mw REAL,
    total_mw REAL,                   -- daily mean generation
    load_mw REAL,                    -- daily mean load
    ren_share_pct REAL,              -- daily avg renewable share of load
    price_avg REAL, price_min REAL, price_max REAL   -- EUR/MWh day-ahead
);

CREATE TABLE IF NOT EXISTS weather_daily (
    date TEXT NOT NULL,
    city TEXT NOT NULL,
    temp_avg REAL, temp_max REAL,
    wind_speed_avg REAL,             -- km/h
    sunshine_min REAL,               -- minutes of sunshine
    precip_mm REAL,
    PRIMARY KEY (date, city)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,        -- ISO UTC
    finished_at TEXT,
    mode TEXT NOT NULL,              -- daily | backfill
    dates_processed INTEGER DEFAULT 0,
    rows_energy INTEGER DEFAULT 0,
    rows_weather INTEGER DEFAULT 0,
    checks_passed INTEGER DEFAULT 0,
    checks_failed INTEGER DEFAULT 0,
    status TEXT NOT NULL,            -- ok | degraded | failed
    notes TEXT DEFAULT ''
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_energy(conn: sqlite3.Connection, row: dict) -> None:
    conn.execute(
        """INSERT INTO energy_daily VALUES
           (:date,:solar_mw,:wind_onshore_mw,:wind_offshore_mw,:hydro_mw,
            :biomass_mw,:gas_mw,:coal_mw,:other_mw,:total_mw,:load_mw,
            :ren_share_pct,:price_avg,:price_min,:price_max)
           ON CONFLICT(date) DO UPDATE SET
            solar_mw=excluded.solar_mw, wind_onshore_mw=excluded.wind_onshore_mw,
            wind_offshore_mw=excluded.wind_offshore_mw, hydro_mw=excluded.hydro_mw,
            biomass_mw=excluded.biomass_mw, gas_mw=excluded.gas_mw,
            coal_mw=excluded.coal_mw, other_mw=excluded.other_mw,
            total_mw=excluded.total_mw, load_mw=excluded.load_mw,
            ren_share_pct=excluded.ren_share_pct, price_avg=excluded.price_avg,
            price_min=excluded.price_min, price_max=excluded.price_max""",
        row,
    )


def upsert_weather(conn: sqlite3.Connection, row: dict) -> None:
    conn.execute(
        """INSERT INTO weather_daily VALUES
           (:date,:city,:temp_avg,:temp_max,:wind_speed_avg,:sunshine_min,:precip_mm)
           ON CONFLICT(date, city) DO UPDATE SET
            temp_avg=excluded.temp_avg, temp_max=excluded.temp_max,
            wind_speed_avg=excluded.wind_speed_avg,
            sunshine_min=excluded.sunshine_min, precip_mm=excluded.precip_mm""",
        row,
    )


def record_run(conn: sqlite3.Connection, run: dict) -> None:
    conn.execute(
        """INSERT INTO runs
           (started_at, finished_at, mode, dates_processed, rows_energy,
            rows_weather, checks_passed, checks_failed, status, notes)
           VALUES (:started_at,:finished_at,:mode,:dates_processed,
                   :rows_energy,:rows_weather,:checks_passed,:checks_failed,
                   :status,:notes)""",
        run,
    )
