/** Reads the pipeline's baked JSON snapshots at build time. */

import fs from "fs";
import path from "path";

export interface RunRecord {
  id: number;
  started_at: string;
  finished_at: string | null;
  mode: string;
  dates_processed: number;
  rows_energy: number;
  rows_weather: number;
  checks_passed: number;
  checks_failed: number;
  status: "ok" | "degraded" | "failed";
  notes: string;
}

export interface StatusSnapshot {
  generatedAt: string;
  sloHours: number;
  freshnessHours: number | null;
  freshnessOk: boolean;
  latestDataDate: string | null;
  totals: { energyDays: number; weatherRows: number; runs: number };
  runs: RunRecord[];
}

export interface EnergyDay {
  date: string;
  solar_mw: number;
  wind_onshore_mw: number;
  wind_offshore_mw: number;
  hydro_mw: number;
  biomass_mw: number;
  gas_mw: number;
  coal_mw: number;
  other_mw: number;
  total_mw: number;
  load_mw: number | null;
  ren_share_pct: number | null;
  price_avg: number | null;
  price_min: number | null;
  price_max: number | null;
}

export interface WindJoinPoint {
  date: string;
  wind_speed_avg: number;
  wind_mw: number;
}

function read<T>(name: string): T | null {
  try {
    const file = path.join(process.cwd(), "public", "data", `${name}.json`);
    return JSON.parse(fs.readFileSync(file, "utf8")) as T;
  } catch {
    return null;
  }
}

export const getStatus = () => read<StatusSnapshot>("status");
export const getEnergy = () => read<EnergyDay[]>("energy");
export const getWindJoin = () => read<WindJoinPoint[]>("wind_join");
