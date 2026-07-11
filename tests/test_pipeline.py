"""Unit tests for Fließband transforms and checks — run in CI on every push."""

import sqlite3
from datetime import datetime, timezone

from pipeline import checks
from pipeline.db import SCHEMA, upsert_energy
from pipeline.sources import berlin_day_of


def make_energy_row(**overrides):
    row = {
        "date": "2026-07-10",
        "solar_mw": 12000.0, "wind_onshore_mw": 8000.0, "wind_offshore_mw": 2000.0,
        "hydro_mw": 1500.0, "biomass_mw": 3500.0, "gas_mw": 6000.0,
        "coal_mw": 7000.0, "other_mw": 1000.0,
        "total_mw": 41000.0, "load_mw": 52000.0, "ren_share_pct": 55.3,
        "price_avg": 82.5, "price_min": -5.0, "price_max": 190.0,
    }
    row.update(overrides)
    return row


def test_berlin_day_rolls_over_at_midnight_berlin_not_utc():
    # 2026-07-10 22:30 UTC is already 2026-07-11 00:30 in Berlin (CEST).
    late_utc = int(datetime(2026, 7, 10, 22, 30, tzinfo=timezone.utc).timestamp())
    assert berlin_day_of(late_utc) == "2026-07-11"


def test_energy_checks_pass_for_plausible_row():
    results = checks.check_energy_row(make_energy_row())
    assert all(ok for _, ok, _ in results)


def test_energy_checks_flag_impossible_total():
    results = checks.check_energy_row(make_energy_row(total_mw=999999.0))
    assert any(not ok for _, ok, _ in results)


def test_energy_checks_flag_absurd_price():
    results = checks.check_energy_row(make_energy_row(price_avg=99999.0))
    assert any(not ok for _, ok, _ in results)


def test_weather_check_flags_broken_sensor():
    bad = {"date": "2026-07-10", "city": "Berlin", "temp_avg": 71.0}
    results = checks.check_weather_row(bad)
    assert any(not ok for _, ok, _ in results)


def test_upsert_is_idempotent():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    upsert_energy(conn, make_energy_row())
    upsert_energy(conn, make_energy_row(solar_mw=13000.0))  # corrected value

    rows = conn.execute("SELECT * FROM energy_daily").fetchall()
    assert len(rows) == 1
    assert rows[0]["solar_mw"] == 13000.0
