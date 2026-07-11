"""Upstream sources for Fließband.

- Energy: Energy-Charts API by Fraunhofer ISE (prices CC BY 4.0
  Bundesnetzagentur | SMARD.de). No key.
- Weather: Bright Sky (DWD open data). No key.

Both get polite retries with backoff — a transient upstream failure
must not fail a run.
"""

from __future__ import annotations

import json
import ssl
import time
import urllib.request
from collections import defaultdict

import certifi
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")

CITIES = {
    "Berlin": (52.52, 13.41),
    "Hamburg": (53.55, 9.99),
    "München": (48.14, 11.58),
}

GROUP_BY_PRODUCTION_TYPE = {
    "Solar": "solar_mw",
    "Wind onshore": "wind_onshore_mw",
    "Wind offshore": "wind_offshore_mw",
    "Hydro Run-of-River": "hydro_mw",
    "Hydro water reservoir": "hydro_mw",
    "Hydro pumped storage": "hydro_mw",
    "Biomass": "biomass_mw",
    "Geothermal": "biomass_mw",
    "Fossil gas": "gas_mw",
    "Fossil coal-derived gas": "gas_mw",
    "Fossil oil": "gas_mw",
    "Fossil brown coal / lignite": "coal_mw",
    "Fossil hard coal": "coal_mw",
    "Waste": "other_mw",
    "Others": "other_mw",
}

ENERGY_KEYS = [
    "solar_mw", "wind_onshore_mw", "wind_offshore_mw", "hydro_mw",
    "biomass_mw", "gas_mw", "coal_mw", "other_mw",
]


_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def fetch_json(url: str, attempts: int = 3, timeout: int = 45) -> dict:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(
                url, headers={"Accept": "application/json",
                              "User-Agent": "fliessband-pipeline"}
            )
            with urllib.request.urlopen(
                req, timeout=timeout, context=_SSL_CONTEXT
            ) as res:
                return json.load(res)
        except Exception as error:  # noqa: BLE001 — retried, then re-raised
            last_error = error
            if attempt < attempts:
                time.sleep(2 * attempt)
    raise RuntimeError(f"GET {url} failed after {attempts} attempts: {last_error}")


def berlin_day_of(unix_seconds: int) -> str:
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc).astimezone(
        BERLIN
    ).strftime("%Y-%m-%d")


def fetch_energy_range(start: date, end: date) -> dict[str, dict]:
    """Daily energy aggregates for [start, end] inclusive, keyed by date."""
    span = f"start={start.isoformat()}&end={(end + timedelta(days=1)).isoformat()}"

    power = fetch_json(f"https://api.energy-charts.info/public_power?country=de&{span}")

    # Prices are enrichment, not the backbone — a rate-limited price call
    # must not cost us the generation data for a whole chunk.
    try:
        time.sleep(1.0)
        price = fetch_json(f"https://api.energy-charts.info/price?bzn=DE-LU&{span}")
    except RuntimeError as error:
        print(f"  ~ price unavailable for {span}: {error}")
        price = {}

    sums: dict[str, defaultdict] = {}
    counts: dict[str, defaultdict] = {}

    def acc(day: str, key: str, value: float) -> None:
        sums.setdefault(day, defaultdict(float))[key] += value
        counts.setdefault(day, defaultdict(int))[key] += 1

    seconds = power.get("unix_seconds", [])
    for ptype in power.get("production_types", []):
        key = GROUP_BY_PRODUCTION_TYPE.get(ptype["name"])
        is_load = ptype["name"] == "Load"
        is_share = ptype["name"] == "Renewable share of load"
        if not key and not is_load and not is_share:
            continue
        for i, value in enumerate(ptype["data"]):
            if value is None or i >= len(seconds):
                continue
            day = berlin_day_of(seconds[i])
            if is_load:
                acc(day, "load_mw", value)
            elif is_share:
                acc(day, "ren_share_pct", value)
            elif value > 0:
                acc(day, key, value)

    price_by_day: dict[str, list[float]] = defaultdict(list)
    for i, value in enumerate(price.get("price", [])):
        if value is not None and i < len(price["unix_seconds"]):
            price_by_day[berlin_day_of(price["unix_seconds"][i])].append(value)

    rows: dict[str, dict] = {}
    day_cursor = start
    while day_cursor <= end:
        day = day_cursor.isoformat()
        day_sums, day_counts = sums.get(day), counts.get(day)
        if day_sums:
            row = {"date": day}
            for key in ENERGY_KEYS:
                n = day_counts.get(key, 0)
                row[key] = round(day_sums.get(key, 0.0) / n, 1) if n else 0.0
            row["total_mw"] = round(sum(row[k] for k in ENERGY_KEYS), 1)
            for key in ("load_mw", "ren_share_pct"):
                n = day_counts.get(key, 0)
                row[key] = round(day_sums.get(key, 0.0) / n, 1) if n else None
            day_prices = price_by_day.get(day, [])
            row["price_avg"] = round(sum(day_prices) / len(day_prices), 2) if day_prices else None
            row["price_min"] = round(min(day_prices), 2) if day_prices else None
            row["price_max"] = round(max(day_prices), 2) if day_prices else None
            rows[day] = row
        day_cursor += timedelta(days=1)
    return rows


def fetch_weather_range(start: date, end: date, city: str) -> dict[str, dict]:
    """Daily weather aggregates per city for [start, end], keyed by date."""
    lat, lon = CITIES[city]
    raw = fetch_json(
        "https://api.brightsky.dev/weather"
        f"?lat={lat}&lon={lon}&date={start.isoformat()}"
        f"&last_date={(end + timedelta(days=1)).isoformat()}&tz=Europe/Berlin"
    )

    by_day: dict[str, list[dict]] = defaultdict(list)
    for record in raw.get("weather", []):
        by_day[record["timestamp"][:10]].append(record)

    rows: dict[str, dict] = {}
    for day, records in by_day.items():
        if not (start.isoformat() <= day <= end.isoformat()):
            continue

        def series(field: str) -> list[float]:
            return [r[field] for r in records if r.get(field) is not None]

        temps, winds = series("temperature"), series("wind_speed")
        sunshine, precip = series("sunshine"), series("precipitation")
        if not temps:
            continue
        rows[day] = {
            "date": day,
            "city": city,
            "temp_avg": round(sum(temps) / len(temps), 1),
            "temp_max": round(max(temps), 1),
            "wind_speed_avg": round(sum(winds) / len(winds), 1) if winds else None,
            "sunshine_min": round(sum(sunshine), 0) if sunshine else None,
            "precip_mm": round(sum(precip), 1) if precip else None,
        }
    return rows
