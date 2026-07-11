"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { EnergyDay, WindJoinPoint } from "@/lib/data";

const AXIS = { stroke: "#c3cad2", fontSize: 11, fontFamily: "var(--font-mono)" };
const GRID = { stroke: "#e3e7eb", strokeDasharray: "3 3" };
const TOOLTIP_STYLE = {
  background: "#171b1f",
  border: "none",
  borderRadius: 6,
  fontFamily: "var(--font-mono)",
  fontSize: 12,
  color: "#eef0f2",
};

const monthLabel = (date: string) =>
  new Date(date).toLocaleDateString("en-GB", { month: "short" });

export function WindScatter({ points }: { points: WindJoinPoint[] }) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <ScatterChart margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid {...GRID} />
          <XAxis
            dataKey="wind_speed_avg"
            name="wind speed"
            unit=" km/h"
            type="number"
            tick={AXIS}
            axisLine={{ stroke: "#c3cad2" }}
            tickLine={false}
          />
          <YAxis
            dataKey="wind_mw"
            name="wind generation"
            type="number"
            tick={AXIS}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => `${Math.round(v / 1000)} GW`}
            width={56}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value: number, name: string) =>
              name === "wind generation"
                ? [`${(value / 1000).toFixed(1)} GW`, name]
                : [`${value} km/h`, name]
            }
            labelFormatter={() => ""}
          />
          <Scatter data={points} fill="#ff5c00" fillOpacity={0.55} shape="circle" />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RenShareArea({ energy }: { energy: EnergyDay[] }) {
  const data = energy.filter((d) => d.ren_share_pct != null);
  return (
    <div className="h-60 w-full">
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <defs>
            <linearGradient id="ren" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1a7f37" stopOpacity={0.5} />
              <stop offset="100%" stopColor="#1a7f37" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid {...GRID} />
          <XAxis
            dataKey="date"
            tick={AXIS}
            tickFormatter={monthLabel}
            axisLine={{ stroke: "#c3cad2" }}
            tickLine={false}
            minTickGap={40}
          />
          <YAxis
            tick={AXIS}
            axisLine={false}
            tickLine={false}
            unit=" %"
            width={48}
            domain={[0, 120]}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value: number) => [`${value.toFixed(1)} %`, "renewable share"]}
          />
          <Area
            dataKey="ren_share_pct"
            stroke="#1a7f37"
            strokeWidth={1.5}
            fill="url(#ren)"
            dot={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function PriceLine({ energy }: { energy: EnergyDay[] }) {
  return (
    <div className="h-60 w-full">
      <ResponsiveContainer>
        <LineChart data={energy} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
          <CartesianGrid {...GRID} />
          <XAxis
            dataKey="date"
            tick={AXIS}
            tickFormatter={monthLabel}
            axisLine={{ stroke: "#c3cad2" }}
            tickLine={false}
            minTickGap={40}
          />
          <YAxis
            tick={AXIS}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v: number) => `${v} €`}
            width={56}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value: number) => [`${value.toFixed(2)} € / MWh`, "avg price"]}
          />
          <Line
            dataKey="price_avg"
            stroke="#171b1f"
            strokeWidth={1.5}
            dot={false}
            connectNulls={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
