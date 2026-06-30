import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { FileDown, ShieldCheck, History } from "lucide-react";

const CITIES = ["Mumbai (MMR)", "Delhi NCR", "Bengaluru", "Hyderabad", "Chennai", "Pune"];
const PROPS = ["Apartment", "Villa", "Office", "Retail Shop", "Warehouse", "Plot"];

export default function ValuationMemo() {
  const [form, setForm] = useState({
    city: "Mumbai (MMR)", submarket: "", property_type: "Apartment",
    size_sqft: 1200, verified_only: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const loadHistory = async () => {
    try {
      const { data } = await api.get("/memos");
      setHistory(Array.isArray(data) ? data : []);
    } catch {
      setHistory([]);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const generate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/valuation-memo", {
        ...form,
        size_sqft: Number(form.size_sqft),
        submarket: form.submarket || null,
      }, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `valuation_memo_${form.city.replace(/ /g, "_")}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      loadHistory();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Failed to generate memo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div data-testid="memo-page">
      <div className="px-6 lg:px-8 py-6 border-b border-[var(--ph-line)]">
        <div className="tiny-caps text-[var(--ph-muted)]">Valuation Memo</div>
        <h1 className="font-display text-2xl lg:text-3xl font-bold mt-2 tracking-tight">
          One-click defensible memo PDF.
        </h1>
        <p className="text-sm text-[var(--ph-ink-2)] mt-3 max-w-2xl">
          Generate a printable, source-attributed valuation memo with comparable transactions and nearby developments — ready for client decks.
        </p>
      </div>

      <form onSubmit={generate} className="max-w-2xl p-6 lg:p-8 space-y-5" data-testid="memo-form">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="tiny-caps text-[var(--ph-muted)]">City</label>
            <select className="input-ph mt-2" value={form.city} onChange={set("city")} data-testid="memo-city">
              {CITIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="tiny-caps text-[var(--ph-muted)]">Submarket (optional)</label>
            <input className="input-ph mt-2" placeholder="e.g. Whitefield, Lower Parel" value={form.submarket} onChange={set("submarket")} data-testid="memo-submarket" />
          </div>
          <div>
            <label className="tiny-caps text-[var(--ph-muted)]">Property type</label>
            <select className="input-ph mt-2" value={form.property_type} onChange={set("property_type")} data-testid="memo-property-type">
              {PROPS.map((p) => <option key={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="tiny-caps text-[var(--ph-muted)]">Subject size (sqft)</label>
            <input className="input-ph mt-2 font-mono-ph" type="number" value={form.size_sqft} onChange={set("size_sqft")} data-testid="memo-size" />
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={form.verified_only} onChange={(e) => setForm({ ...form, verified_only: e.target.checked })} data-testid="memo-verified" />
          <ShieldCheck size={14} className="text-[var(--ph-success)]" />
          Use VERIFIED sources only (Sub-Registrar + NHAI) — recommended for client deliverables
        </label>

        {error && <div className="text-sm text-[var(--ph-accent)]" data-testid="memo-error">{error}</div>}

        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2 disabled:opacity-60" data-testid="memo-generate">
          <FileDown size={16} />
          {loading ? "Generating memo…" : "Generate PDF memo"}
        </button>

        <div className="text-xs text-[var(--ph-muted)] pt-4 border-t border-[var(--ph-line)]">
          Memo includes: indicative value, ₹/sqft range, up to 200 comparable transactions with confidence badges, up to 50 nearby developments, and full source attribution per the analyst's audit trail. Tables auto-paginate across multiple pages.
        </div>
      </form>

      <div className="px-6 lg:px-8 py-6 border-t border-[var(--ph-line)]" data-testid="memo-history">
        <div className="flex items-center gap-2 mb-4">
          <History size={16} />
          <div className="tiny-caps text-[var(--ph-muted)]">My memos</div>
          <span className="text-xs text-[var(--ph-muted)] font-mono-ph">({history.length})</span>
        </div>
        {history.length === 0 ? (
          <div className="text-sm text-[var(--ph-muted)]">No memos generated yet. Your history will appear here.</div>
        ) : (
          <div className="panel divide-y divide-[var(--ph-line)] max-w-3xl">
            {history.map((m, i) => (
              <div key={m.filename || i} className="p-4 grid grid-cols-[1fr_auto] gap-4 items-center" data-testid={`memo-history-${i}`}>
                <div>
                  <div className="font-medium text-sm">
                    {m.submarket ? `${m.submarket}, ` : ""}{m.city} · {m.property_type}
                  </div>
                  <div className="text-xs text-[var(--ph-muted)] mt-1 font-mono-ph">
                    {m.size_sqft} sqft · {m.comps_count} comps · {m.verified_only ? "VERIFIED only" : "All sources"} · {new Date(m.generated_at).toLocaleString()}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono-ph font-bold text-sm">
                    {m.indicative_value >= 1e7 ? `₹${(m.indicative_value/1e7).toFixed(2)} Cr` : m.indicative_value >= 1e5 ? `₹${(m.indicative_value/1e5).toFixed(1)} L` : "—"}
                  </div>
                  <div className="text-xs text-[var(--ph-muted)] font-mono-ph">@ ₹{Math.round(m.avg_psf || 0).toLocaleString("en-IN")}/sqft</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
