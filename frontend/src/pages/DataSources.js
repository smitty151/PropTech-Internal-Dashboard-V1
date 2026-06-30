import { useEffect, useRef, useState } from "react";
import { api, API } from "../lib/api";
import { RefreshCw, Upload, FileText, CheckCircle2, Database } from "lucide-react";

export default function DataSources() {
  const [sources, setSources] = useState([]);
  const [busy, setBusy] = useState({});
  const [toast, setToast] = useState(null);
  const fileRef = useRef(null);

  const load = async () => {
    const { data } = await api.get("/data-sources");
    setSources(data);
  };

  useEffect(() => { load(); }, []);

  const refresh = async (key) => {
    setBusy({ ...busy, [key]: true });
    try {
      const { data } = await api.post(`/data-sources/${key}/refresh`);
      setToast({ ok: true, text: `${data.source}: ${data.ingested} records ingested.` });
      await load();
    } catch (e) {
      setToast({ ok: false, text: e.response?.data?.detail || e.message });
    } finally {
      setBusy({ ...busy, [key]: false });
      setTimeout(() => setToast(null), 4500);
    }
  };

  const uploadCsv = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy({ ...busy, csv_import: true });
    try {
      const fd = new FormData();
      fd.append("file", f);
      const { data } = await api.post("/data-sources/csv/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const errSuffix = data.errors?.length ? ` · ${data.errors.length} row errors skipped` : "";
      setToast({ ok: true, text: `Imported ${data.ingested} comps from ${data.filename}.${errSuffix}` });
      await load();
    } catch (err) {
      setToast({ ok: false, text: err.response?.data?.detail || err.message });
    } finally {
      setBusy({ ...busy, csv_import: false });
      if (fileRef.current) fileRef.current.value = "";
      setTimeout(() => setToast(null), 5500);
    }
  };

  return (
    <div data-testid="data-sources-page">
      <div className="px-6 lg:px-8 py-6 border-b border-[var(--ph-line)]">
        <div className="tiny-caps text-[var(--ph-muted)]">Phase 2 · Real Data</div>
        <h1 className="font-display text-2xl lg:text-3xl font-bold mt-2 tracking-tight">
          Data Sources
        </h1>
        <p className="text-sm text-[var(--ph-ink-2)] mt-3 max-w-2xl">
          Connect, refresh, and audit every source feeding the platform. Each ingested record
          is tagged with its provenance so your valuations stay defensible.
        </p>
      </div>

      {toast && (
        <div
          data-testid="ds-toast"
          className={`mx-6 lg:mx-8 mt-6 p-3 text-sm border ${
            toast.ok ? "border-[var(--ph-success)] text-[var(--ph-success)]" : "border-[var(--ph-accent)] text-[var(--ph-accent)]"
          }`}
        >
          {toast.ok && <CheckCircle2 size={14} className="inline -mt-0.5 mr-2" />}
          {toast.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
        {sources.map((s) => (
          <div key={s.key} className="cell p-6 lg:p-8" data-testid={`ds-card-${s.key}`}>
            <div className="flex items-center justify-between">
              <Database size={18} strokeWidth={1.5} />
              <span className="tiny-caps text-[var(--ph-muted)]">{s.target}</span>
            </div>
            <div className="font-display font-bold text-lg mt-6">{s.name}</div>
            <div className="text-xs text-[var(--ph-muted)] mt-2 leading-relaxed">
              {s.attribution}
            </div>

            <div className="mt-6 panel p-3 text-xs font-mono-ph bg-[var(--ph-bg-2)]">
              {s.last_run ? (
                <>
                  <div className="flex justify-between"><span>Last run</span><span>{new Date(s.last_run.last_run_at).toLocaleString()}</span></div>
                  <div className="flex justify-between mt-1"><span>Records</span><span>{s.last_run.records_ingested}</span></div>
                  <div className="flex justify-between mt-1"><span>Action</span><span>{s.last_run.last_action}</span></div>
                </>
              ) : (
                <div className="text-[var(--ph-muted)]">No runs yet.</div>
              )}
            </div>

            <div className="mt-6">
              {s.key === "csv_import" ? (
                <div className="flex flex-col gap-2">
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".csv"
                    onChange={uploadCsv}
                    className="hidden"
                    data-testid="ds-csv-input"
                  />
                  <button
                    onClick={() => fileRef.current?.click()}
                    disabled={busy.csv_import}
                    className="btn-primary text-sm flex items-center gap-2 disabled:opacity-60"
                    data-testid="ds-upload-csv"
                  >
                    <Upload size={14} /> {busy.csv_import ? "Uploading…" : "Upload CSV"}
                  </button>
                  <a
                    href={`${API}/data-sources/csv/template`}
                    className="text-xs underline flex items-center gap-1 text-[var(--ph-ink-2)]"
                    data-testid="ds-csv-template"
                  >
                    <FileText size={12} /> Download CSV template
                  </a>
                </div>
              ) : (
                <button
                  onClick={() => refresh(s.key)}
                  disabled={busy[s.key]}
                  className="btn-primary text-sm flex items-center gap-2 disabled:opacity-60"
                  data-testid={`ds-refresh-${s.key}`}
                >
                  <RefreshCw size={14} className={busy[s.key] ? "animate-spin" : ""} />
                  {busy[s.key] ? "Ingesting…" : "Refresh now"}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="px-6 lg:px-8 py-8 border-t border-[var(--ph-line)] mt-0">
        <div className="tiny-caps text-[var(--ph-muted)]">CSV format</div>
        <div className="font-display text-lg font-bold mt-2">Required columns</div>
        <code className="block mt-3 p-3 panel font-mono-ph text-xs overflow-x-auto">
          city, submarket, property_type, transaction_type, size_sqft, asking_price_inr, sold_price_inr
        </code>
        <div className="text-xs text-[var(--ph-ink-2)] mt-2">
          Optional: <span className="font-mono-ph">address, building_age_yrs, land_size_acres, owner, transaction_date</span>
        </div>
      </div>
    </div>
  );
}
