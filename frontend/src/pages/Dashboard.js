import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, inrCr } from "../lib/api";
import { Map, Database, Calculator, TrendingUp, ArrowUpRight } from "lucide-react";

const TYPE_COLORS = {
  Metro: "#002FA7", Highway: "#7C3AED", Railway: "#0E7490",
  Airport: "#0284C7", Residential: "#16A34A", Commercial: "#0A0A0A",
  Retail: "#E11D48", Industrial: "#92400E", Hospital: "#DB2777",
  Land: "#65A30D", Hospitality: "#F59E0B",
};

export default function Dashboard() {
  const [devStats, setDevStats] = useState(null);
  const [compStats, setCompStats] = useState(null);
  const [reits, setReits] = useState([]);

  useEffect(() => {
    (async () => {
      const [a, b, c] = await Promise.all([
        api.get("/developments/stats"),
        api.get("/comps/stats"),
        api.get("/reits"),
      ]);
      setDevStats(a.data);
      setCompStats(b.data);
      setReits(c.data);
    })();
  }, []);

  return (
    <div data-testid="dashboard">
      <div className="px-6 lg:px-8 py-8 border-b border-[var(--ph-line)]">
        <div className="tiny-caps text-[var(--ph-muted)]">Overview</div>
        <h1 className="font-display text-3xl lg:text-4xl font-bold mt-2 tracking-tight">
          India real estate intelligence, at a glance.
        </h1>
        <p className="text-sm text-[var(--ph-ink-2)] mt-3 max-w-2xl">
          Six metros, hundreds of projects, every active comp. Open any module below to drill in.
        </p>
      </div>

      {/* Top metrics — Control Room grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 border-b border-[var(--ph-line)]">
        {[
          { label: "Projects tracked", value: devStats?.total ?? "—", testId: "metric-projects" },
          { label: "Total project value", value: devStats ? inrCr(devStats.by_type.reduce((s, x) => s + x.value, 0)) : "—", testId: "metric-value" },
          { label: "Sale + Rent comps", value: compStats?.total ?? "—", testId: "metric-comps" },
          { label: "REITs modelled", value: reits.length || "—", testId: "metric-reits" },
        ].map((m) => (
          <div key={m.label} className="cell px-6 py-8" data-testid={m.testId}>
            <div className="tiny-caps text-[var(--ph-muted)]">{m.label}</div>
            <div className="font-display text-3xl lg:text-4xl font-bold mt-3 tracking-tight">{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
        {/* By type */}
        <div className="lg:col-span-2 cell p-6 lg:p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="tiny-caps text-[var(--ph-muted)]">Project pipeline</div>
              <div className="font-display text-xl font-bold">Investment by type</div>
            </div>
            <Link to="/app/developments" className="text-sm underline" data-testid="dashboard-to-developments">
              Open map →
            </Link>
          </div>
          <div className="space-y-3">
            {devStats?.by_type
              ?.sort((a, b) => b.value - a.value)
              .map((row) => {
                const max = Math.max(...devStats.by_type.map((r) => r.value));
                const pct = (row.value / max) * 100;
                return (
                  <div key={row.type} className="flex items-center gap-3">
                    <div className="w-28 text-sm">{row.type}</div>
                    <div className="flex-1 h-7 bg-[var(--ph-bg-3)] relative">
                      <div
                        className="h-full"
                        style={{ width: `${pct}%`, background: TYPE_COLORS[row.type] || "#0A0A0A" }}
                      />
                    </div>
                    <div className="w-28 text-right font-mono-ph text-sm">{inrCr(row.value)}</div>
                    <div className="w-12 text-right font-mono-ph text-xs text-[var(--ph-muted)]">{row.count}</div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* By city */}
        <div className="cell p-6 lg:p-8">
          <div className="tiny-caps text-[var(--ph-muted)]">By city</div>
          <div className="font-display text-xl font-bold mb-4">Coverage</div>
          <div className="divide-y divide-[var(--ph-line)]">
            {devStats?.by_city
              ?.sort((a, b) => b.count - a.count)
              .map((c) => (
                <div key={c.city} className="flex justify-between py-2.5 text-sm">
                  <span>{c.city}</span>
                  <span className="font-mono-ph">{c.count} projects</span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-3">
        {[
          { to: "/app/developments", icon: Map, title: "Developments Map", body: "Geocoded infrastructure & RE projects.", testId: "card-developments" },
          { to: "/app/comps", icon: Database, title: "Sale & Rent Comps", body: "Filterable transactions database.", testId: "card-comps" },
          { to: "/app/calculator", icon: Calculator, title: "Cost of Capital", body: "REIT-anchored WACC & discount rate.", testId: "card-calculator" },
        ].map(({ to, icon: Icon, title, body, testId }) => (
          <Link
            key={to}
            to={to}
            data-testid={testId}
            className="cell p-8 group transition-colors flex flex-col"
          >
            <div className="flex items-center justify-between">
              <Icon size={20} strokeWidth={1.5} />
              <ArrowUpRight size={18} className="opacity-30 group-hover:opacity-100 transition-opacity" />
            </div>
            <div className="font-display text-xl font-bold mt-8">{title}</div>
            <div className="text-sm text-[var(--ph-ink-2)] mt-2">{body}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
