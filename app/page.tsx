import { clsx } from "clsx";

import { getEnergy, getStatus, getWindJoin, type RunRecord } from "@/lib/data";
import { PriceLine, RenShareArea, WindScatter } from "@/components/charts";

const fmtUTC = (iso: string) =>
  new Date(iso).toISOString().replace("T", " ").slice(0, 16) + " UTC";

function StatusChip({ status }: { status: RunRecord["status"] }) {
  return (
    <span
      className={clsx(
        "rounded-sm px-2 py-0.5 font-mono text-[10px] font-semibold tracking-wider uppercase",
        status === "ok" && "bg-ok/10 text-ok",
        status === "degraded" && "bg-[#f5b301]/15 text-[#946c00]",
        status === "failed" && "bg-alarm/10 text-alarm"
      )}
    >
      {status}
    </span>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-mono text-[10px] font-semibold tracking-[0.22em] text-faded uppercase">
      {children}
    </p>
  );
}

export default function StatusPage() {
  const status = getStatus();
  const energy = getEnergy() ?? [];
  const windJoin = getWindJoin() ?? [];

  const lastRun = status?.runs?.[0] ?? null;
  const streak = (() => {
    let n = 0;
    for (const run of status?.runs ?? []) {
      if (run.status === "ok") n++;
      else break;
    }
    return n;
  })();

  const operational = Boolean(status?.freshnessOk && lastRun?.status !== "failed");

  return (
    <>
      <header className="border-b border-seam bg-sheet">
        <div className="container-line flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-3">
            <span className="bg-safety px-2 py-1 font-mono text-sm font-bold tracking-wider text-white">
              FB
            </span>
            <p className="text-lg font-bold tracking-tight">
              Fließband
              <span className="ml-3 hidden font-mono text-[10px] font-medium tracking-[0.22em] text-faded uppercase sm:inline">
                Daten-Pipeline · Status
              </span>
            </p>
          </div>
          {status && (
            <p className="font-mono text-xs text-faded">
              snapshot {fmtUTC(status.generatedAt)}
            </p>
          )}
        </div>
      </header>

      <main className="container-line flex-1 py-8">
        {!status ? (
          <div className="sheet px-6 py-20 text-center">
            <p className="text-lg font-semibold">No data yet</p>
            <p className="mt-1 font-mono text-xs text-faded">
              Run <code>python3 -m pipeline.ingest --backfill 365</code> first.
            </p>
          </div>
        ) : (
          <>
            <section
              className="sheet reveal overflow-hidden"
              style={{ "--stagger": 0 } as React.CSSProperties}
            >
              <div
                className={clsx("h-2.5", operational ? "stripe-ok" : "hazard")}
              />
              <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-5">
                <div>
                  <Label>Pipeline status</Label>
                  <p
                    className={clsx(
                      "mt-1 text-3xl font-bold tracking-tight",
                      operational ? "text-ok" : "text-[#946c00]"
                    )}
                  >
                    {operational ? "Operational" : "Degraded"}
                  </p>
                </div>
                <div className="flex flex-wrap gap-8 font-mono text-sm">
                  <div>
                    <Label>Freshness</Label>
                    <p className="mt-1 text-xl font-semibold tabular-nums">
                      {status.freshnessHours != null
                        ? `${status.freshnessHours} h`
                        : "—"}
                      <span className="ml-1 text-xs text-faded">
                        / SLO {status.sloHours} h
                      </span>
                    </p>
                  </div>
                  <div>
                    <Label>OK streak</Label>
                    <p className="mt-1 text-xl font-semibold tabular-nums">
                      {streak} <span className="text-xs text-faded">runs</span>
                    </p>
                  </div>
                  <div>
                    <Label>Dataset</Label>
                    <p className="mt-1 text-xl font-semibold tabular-nums">
                      {status.totals.energyDays}
                      <span className="ml-1 text-xs text-faded">days ·</span>{" "}
                      {status.totals.weatherRows}
                      <span className="ml-1 text-xs text-faded">obs</span>
                    </p>
                  </div>
                </div>
              </div>
            </section>

            <section
              className="sheet reveal mt-4 px-6 py-4"
              style={{ "--stagger": 1 } as React.CSSProperties}
            >
              <p className="font-mono text-xs leading-relaxed text-faded">
                <span className="font-semibold text-ink">every day 05:30 UTC</span>{" "}
                → GitHub Actions runs the Python ingest → Energy-Charts +
                Bright Sky (DWD) → quality checks → upsert into{" "}
                <span className="font-semibold text-ink">
                  SQLite, committed to the repo
                </span>{" "}
                → JSON snapshots → this page redeploys. Every run is a public
                commit — the git log is the ops log.
              </p>
            </section>

            <div className="mt-6 grid gap-6 lg:grid-cols-2">
              <section
                className="sheet reveal p-5"
                style={{ "--stagger": 2 } as React.CSSProperties}
              >
                <div className="mb-3 flex items-baseline justify-between">
                  <Label>Wind speed vs. wind generation</Label>
                  <p className="font-mono text-[10px] text-faded">
                    {windJoin.length} joined days · 3 cities avg
                  </p>
                </div>
                <WindScatter points={windJoin} />
              </section>

              <section
                className="sheet reveal p-5"
                style={{ "--stagger": 3 } as React.CSSProperties}
              >
                <div className="mb-3 flex items-baseline justify-between">
                  <Label>Renewable share of load — 365 days</Label>
                  <p className="font-mono text-[10px] text-faded">daily avg</p>
                </div>
                <RenShareArea energy={energy} />
              </section>
            </div>

            <section
              className="sheet reveal mt-6 p-5"
              style={{ "--stagger": 4 } as React.CSSProperties}
            >
              <div className="mb-3 flex items-baseline justify-between">
                <Label>Day-ahead price — 365 days</Label>
                <p className="font-mono text-[10px] text-faded">
                  daily avg, EUR/MWh · gaps = upstream rate limits, honestly shown
                </p>
              </div>
              <PriceLine energy={energy} />
            </section>

            <section
              className="sheet reveal mt-6 overflow-x-auto"
              style={{ "--stagger": 5 } as React.CSSProperties}
            >
              <div className="px-5 pt-4 pb-2">
                <Label>Run history</Label>
              </div>
              <table className="w-full font-mono text-xs">
                <thead>
                  <tr className="border-b border-seam text-left text-[10px] tracking-wider text-faded uppercase">
                    <th className="px-5 py-2 font-medium">Started</th>
                    <th className="px-3 py-2 font-medium">Mode</th>
                    <th className="px-3 py-2 text-right font-medium">Energy</th>
                    <th className="px-3 py-2 text-right font-medium">Weather</th>
                    <th className="px-3 py-2 text-right font-medium">Checks</th>
                    <th className="px-5 py-2 text-right font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {status.runs.slice(0, 12).map((run) => (
                    <tr key={run.id} className="border-b border-seam/60">
                      <td className="px-5 py-2 whitespace-nowrap">
                        {fmtUTC(run.started_at)}
                      </td>
                      <td className="px-3 py-2">{run.mode}</td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {run.rows_energy}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {run.rows_weather}
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {run.checks_passed}✓
                        {run.checks_failed > 0 && (
                          <span className="text-alarm"> {run.checks_failed}✗</span>
                        )}
                      </td>
                      <td className="px-5 py-2 text-right">
                        <StatusChip status={run.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </>
        )}
      </main>

      <footer className="border-t border-seam bg-sheet">
        <div className="container-line flex flex-wrap items-center justify-between gap-2 py-5 font-mono text-[11px] text-faded">
          <p>
            data:{" "}
            <a
              href="https://www.energy-charts.info"
              target="_blank"
              rel="noopener noreferrer"
              className="text-ink underline decoration-seam underline-offset-4 hover:text-safety"
            >
              Energy-Charts · Fraunhofer ISE
            </a>{" "}
            (prices CC BY 4.0 SMARD.de) ·{" "}
            <a
              href="https://brightsky.dev"
              target="_blank"
              rel="noopener noreferrer"
              className="text-ink underline decoration-seam underline-offset-4 hover:text-safety"
            >
              Bright Sky · DWD
            </a>
          </p>
          <p>
            built by{" "}
            <a
              href="https://vivekreddy.de"
              target="_blank"
              rel="noopener noreferrer"
              className="text-ink underline decoration-seam underline-offset-4 hover:text-safety"
            >
              Vivekananda Reddy
            </a>
          </p>
        </div>
      </footer>
    </>
  );
}
