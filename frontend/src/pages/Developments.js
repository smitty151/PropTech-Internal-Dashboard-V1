import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import { api, inrCr } from "../lib/api";
import { ConfidenceBadge, ConfidenceToggle } from "../components/Confidence";

const TYPE_COLORS = {
  Metro: "#002FA7", Highway: "#7C3AED", Railway: "#0E7490",
  Airport: "#0284C7", Residential: "#16A34A", Commercial: "#0A0A0A",
  Retail: "#E11D48", Industrial: "#92400E", Hospital: "#DB2777",
  Land: "#65A30D", Hospitality: "#F59E0B",
};
const ALL_TYPES = Object.keys(TYPE_COLORS);

const CITY_CENTERS = {
  "Mumbai (MMR)": [19.0760, 72.8777],
  "Delhi NCR": [28.6139, 77.2090],
  "Bengaluru": [12.9716, 77.5946],
  "Hyderabad": [17.3850, 78.4867],
  "Chennai": [13.0827, 80.2707],
  "Pune": [18.5204, 73.8567],
};

function FlyTo({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.flyTo(center, 11, { duration: 0.8 });
  }, [center, map]);
  return null;
}

export default function Developments() {
  const [items, setItems] = useState([]);
  const [city, setCity] = useState("Mumbai (MMR)");
  const [type, setType] = useState("all");
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      const params = {};
      if (city !== "all") params.city = city;
      if (type !== "all") params.type = type;
      if (verifiedOnly) params.verified_only = true;
      const { data } = await api.get("/developments", { params });
      setItems(data);
      setLoading(false);
    })();
  }, [city, type, verifiedOnly]);

  const center = useMemo(() => CITY_CENTERS[city] || [20.5937, 78.9629], [city]);

  return (
    <div data-testid="developments-page" className="h-[calc(100vh-3.5rem)] flex flex-col">
      <div className="px-6 py-4 border-b border-[var(--ph-line)] flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="tiny-caps text-[var(--ph-muted)]">Developments Map</div>
          <h1 className="font-display text-2xl font-bold tracking-tight">
            {city === "all" ? "All India" : city} — {items.length} projects
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <ConfidenceToggle value={verifiedOnly} onChange={setVerifiedOnly} testId="dev-confidence" />
          <select
            data-testid="filter-city"
            className="input-ph !w-auto"
            value={city}
            onChange={(e) => setCity(e.target.value)}
          >
            {Object.keys(CITY_CENTERS).map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            data-testid="filter-type"
            className="input-ph !w-auto"
            value={type}
            onChange={(e) => setType(e.target.value)}
          >
            <option value="all">All types</option>
            {ALL_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_360px]">
        <div className="relative">
          <MapContainer center={center} zoom={11} style={{ height: "100%", width: "100%" }}>
            <TileLayer
              attribution='&copy; OpenStreetMap'
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            />
            <FlyTo center={center} />
            {items.map((d) => (
              <CircleMarker
                key={d.external_id || `${d.city_key || d.city}-${d.lat}-${d.lng}-${d.name}`}
                center={[d.lat, d.lng]}
                radius={6}
                pathOptions={{
                  color: "#fff",
                  weight: 1.5,
                  fillColor: TYPE_COLORS[d.type] || "#0A0A0A",
                  fillOpacity: 0.95,
                }}
                eventHandlers={{ click: () => setSelected(d) }}
              >
                <Popup>
                  <div className="font-display font-bold">{d.name}</div>
                  <div className="text-xs">{d.type} · {d.status}</div>
                  <div className="text-xs mt-1">{inrCr(d.investment_inr_cr)}</div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>

          {/* Type legend overlay */}
          <div className="absolute bottom-4 left-4 panel p-3 z-[400]">
            <div className="tiny-caps text-[var(--ph-muted)] mb-2">Legend</div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1">
              {ALL_TYPES.map((t) => (
                <div key={t} className="flex items-center gap-2 text-xs">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: TYPE_COLORS[t] }} />
                  {t}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right rail */}
        <aside className="border-l border-[var(--ph-line)] overflow-y-auto bg-[var(--ph-bg-2)]" data-testid="developments-list">
          {loading && <div className="p-6 text-sm">Loading…</div>}
          {!loading && selected && (
            <div className="p-6 border-b border-[var(--ph-line)] bg-white">
              <div className="flex items-start justify-between gap-2">
                <div className="tiny-caps" style={{ color: TYPE_COLORS[selected.type] }}>{selected.type}</div>
                <ConfidenceBadge source={selected.source} />
              </div>
              <div className="font-display font-bold text-lg mt-1">{selected.name}</div>
              <div className="text-xs text-[var(--ph-muted)] mt-1">{selected.submarket} · {selected.city}</div>
              <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
                <div><div className="tiny-caps text-[var(--ph-muted)]">Status</div><div>{selected.status}</div></div>
                <div><div className="tiny-caps text-[var(--ph-muted)]">Completion</div><div>{selected.completion_year}</div></div>
                <div><div className="tiny-caps text-[var(--ph-muted)]">Investment</div><div className="font-mono-ph">{inrCr(selected.investment_inr_cr)}</div></div>
                <div><div className="tiny-caps text-[var(--ph-muted)]">Size</div><div className="font-mono-ph">{selected.size}</div></div>
                <div className="col-span-2"><div className="tiny-caps text-[var(--ph-muted)]">Developer</div><div>{selected.developer}</div></div>
                {selected.source && (
                  <div className="col-span-2"><div className="tiny-caps text-[var(--ph-muted)]">Source</div><div className="text-xs font-mono-ph">{selected.source}</div></div>
                )}
              </div>
              <p className="text-sm text-[var(--ph-ink-2)] mt-4 leading-relaxed">{selected.description}</p>
            </div>
          )}
          <div className="divide-y divide-[var(--ph-line)]">
            {items.slice(0, 60).map((d, i) => (
              <button
                key={d.external_id || `${d.name}-${d.lat}-${d.lng}`}
                onClick={() => setSelected(d)}
                data-testid={`dev-row-${i}`}
                className="w-full text-left p-4 hover:bg-white transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="tiny-caps" style={{ color: TYPE_COLORS[d.type] }}>{d.type}</div>
                  <div className="text-xs text-[var(--ph-muted)] font-mono-ph">{d.status}</div>
                </div>
                <div className="font-medium text-sm mt-1 truncate">{d.name}</div>
                <div className="text-xs text-[var(--ph-muted)] mt-1">{inrCr(d.investment_inr_cr)} · {d.completion_year}</div>
              </button>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
