import { useEffect, useMemo, useState } from "react";
import { api, inrCompact } from "../lib/api";
import { ConfidenceBadge, ConfidenceToggle } from "../components/Confidence";

const CITIES = ["all", "Mumbai (MMR)", "Delhi NCR", "Bengaluru", "Hyderabad", "Chennai", "Pune"];
const PROPS = ["all", "Apartment", "Villa", "Office", "Retail Shop", "Warehouse", "Plot"];
const TX = ["all", "Sale", "Rent"];

export default function Comps() {
  const [rows, setRows] = useState([]);
  const [filters, setFilters] = useState({ city: "all", property_type: "all", transaction_type: "all" });
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const params = { ...filters };
      if (verifiedOnly) params.verified_only = true;
      const { data } = await api.get("/comps", { params });
      setRows(data);
      setLoading(false);
    })();
  }, [filters, verifiedOnly]);

  const filtered = useMemo(() => {
    if (!search) return rows;
    const q = search.toLowerCase();
    return rows.filter(
      (r) =>
        r.submarket?.toLowerCase().includes(q) ||
        r.address?.toLowerCase().includes(q) ||
        r.owner?.toLowerCase().includes(q)
    );
  }, [rows, search]);

  const avgPsf = useMemo(() => {
    if (!filtered.length) return 0;
    return Math.round(filtered.reduce((s, r) => s + (r.price_per_sqft || 0), 0) / filtered.length);
  }, [filtered]);

  return (
    <div data-testid="comps-page">
      <div className="px-6 lg:px-8 py-6 border-b border-[var(--ph-line)]">
        <div className="tiny-caps text-[var(--ph-muted)]">Sale & Rent Comps</div>
        <h1 className="font-display text-2xl lg:text-3xl font-bold mt-2 tracking-tight">
          Transactions database — {filtered.length} comps
        </h1>
      </div>

      {/* Stat strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 border-b border-[var(--ph-line)]">
        <div className="cell p-5">
          <div className="tiny-caps text-[var(--ph-muted)]">Avg ₹/sqft</div>
          <div className="font-display text-2xl font-bold mt-2 font-mono-ph">₹{avgPsf.toLocaleString("en-IN")}</div>
        </div>
        <div className="cell p-5">
          <div className="tiny-caps text-[var(--ph-muted)]">Sale comps</div>
          <div className="font-display text-2xl font-bold mt-2">{filtered.filter((r) => r.transaction_type === "Sale").length}</div>
        </div>
        <div className="cell p-5">
          <div className="tiny-caps text-[var(--ph-muted)]">Rent comps</div>
          <div className="font-display text-2xl font-bold mt-2">{filtered.filter((r) => r.transaction_type === "Rent").length}</div>
        </div>
        <div className="cell p-5">
          <div className="tiny-caps text-[var(--ph-muted)]">Markets</div>
          <div className="font-display text-2xl font-bold mt-2">{new Set(filtered.map((r) => r.city)).size}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 lg:px-8 py-4 border-b border-[var(--ph-line)] flex gap-3 flex-wrap items-center">
        <ConfidenceToggle value={verifiedOnly} onChange={setVerifiedOnly} testId="comps-confidence" />
        <input
          data-testid="comps-search"
          className="input-ph !w-64"
          placeholder="Search address / submarket / owner"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select data-testid="comps-filter-city" className="input-ph !w-auto" value={filters.city} onChange={(e) => setFilters({ ...filters, city: e.target.value })}>
          {CITIES.map((c) => <option key={c} value={c}>{c === "all" ? "All cities" : c}</option>)}
        </select>
        <select data-testid="comps-filter-property" className="input-ph !w-auto" value={filters.property_type} onChange={(e) => setFilters({ ...filters, property_type: e.target.value })}>
          {PROPS.map((c) => <option key={c} value={c}>{c === "all" ? "All property types" : c}</option>)}
        </select>
        <select data-testid="comps-filter-tx" className="input-ph !w-auto" value={filters.transaction_type} onChange={(e) => setFilters({ ...filters, transaction_type: e.target.value })}>
          {TX.map((c) => <option key={c} value={c}>{c === "all" ? "All transactions" : c}</option>)}
        </select>
        <button
          data-testid="comps-reset"
          className="btn-outline !py-2 !px-3 text-sm"
          onClick={() => { setFilters({ city: "all", property_type: "all", transaction_type: "all" }); setSearch(""); }}
        >
          Reset
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm" data-testid="comps-table">
          <thead className="bg-[var(--ph-bg-2)] sticky top-0">
            <tr className="text-left">
              {["Confidence", "City / Submarket", "Address", "Type", "TX", "Sqft", "Age", "Asking", "Sold / Rent", "₹/sqft", "Owner", "Date"].map((h) => (
                <th key={h} className="px-4 py-3 tiny-caps text-[var(--ph-muted)] border-b border-[var(--ph-line)]">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={12} className="p-8 text-center">Loading…</td></tr>}
            {!loading && filtered.slice(0, 250).map((r, i) => (
              <tr key={r.external_id || `${r.address}-${r.transaction_date}-${r.sold_price_inr}`} className="border-b border-[var(--ph-line)] hover:bg-[var(--ph-bg-2)]" data-testid={`comp-row-${i}`}>
                <td className="px-4 py-3"><ConfidenceBadge source={r.source} /></td>
                <td className="px-4 py-3">
                  <div className="font-medium">{r.submarket}</div>
                  <div className="text-xs text-[var(--ph-muted)]">{r.city}</div>
                </td>
                <td className="px-4 py-3 text-xs">{r.address}</td>
                <td className="px-4 py-3">{r.property_type}</td>
                <td className="px-4 py-3">
                  <span className={`inline-block px-2 py-0.5 text-xs border ${
                    r.transaction_type === "Sale" ? "border-[var(--ph-brand)] text-[var(--ph-brand)]" : "border-[var(--ph-accent)] text-[var(--ph-accent)]"
                  }`}>
                    {r.transaction_type}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono-ph text-right">{r.size_sqft?.toLocaleString("en-IN")}</td>
                <td className="px-4 py-3 font-mono-ph text-right">{r.building_age_yrs}y</td>
                <td className="px-4 py-3 font-mono-ph text-right">{inrCompact(r.asking_price_inr)}</td>
                <td className="px-4 py-3 font-mono-ph text-right font-semibold">{inrCompact(r.sold_price_inr)}</td>
                <td className="px-4 py-3 font-mono-ph text-right">₹{(r.price_per_sqft || 0).toLocaleString("en-IN")}</td>
                <td className="px-4 py-3 text-xs">{r.owner}</td>
                <td className="px-4 py-3 font-mono-ph text-xs">{r.transaction_date}</td>
              </tr>
            ))}
            {!loading && filtered.length === 0 && (
              <tr><td colSpan={12} className="p-12 text-center text-[var(--ph-muted)]">No comps match these filters.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
