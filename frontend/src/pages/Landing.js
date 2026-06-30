import { Link } from "react-router-dom";
import { ArrowRight, Building2, Map, Database, Calculator } from "lucide-react";

export default function Landing() {
  return (
    <div className="min-h-screen bg-white text-[var(--ph-ink)]">
      {/* Top bar */}
      <header className="border-b border-[var(--ph-line)]">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-6 h-14">
          <div className="flex items-center gap-2">
            <Building2 size={18} strokeWidth={1.5} />
            <span className="font-display font-bold tracking-tight">PlaceHolder</span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="text-sm font-medium" data-testid="header-login-link">Sign in</Link>
            <Link to="/register" className="btn-primary text-sm" data-testid="header-register-cta">
              Request access
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="border-b border-[var(--ph-line)]">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-0">
          <div className="lg:col-span-7 px-6 lg:px-10 py-16 lg:py-24 border-r border-[var(--ph-line)]">
            <div className="tiny-caps text-[var(--ph-muted)] mb-6">India · Commercial · Residential · Infrastructure</div>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.05] tracking-tight">
              The single source of truth<br />
              for Indian real estate.
            </h1>
            <p className="mt-6 text-base lg:text-lg text-[var(--ph-ink-2)] max-w-2xl leading-relaxed">
              Track every airport, metro, highway and tower being built across India&apos;s top markets.
              Pair that with sale & rent comps, REIT-anchored cost-of-capital models, and turn fragmented
              chaos into a defensible valuation edge.
            </p>
            <div className="mt-10 flex flex-wrap items-center gap-3">
              <Link to="/register" className="btn-primary flex items-center gap-2" data-testid="hero-register-cta">
                Get started <ArrowRight size={16} />
              </Link>
              <Link to="/login" className="btn-outline" data-testid="hero-login-cta">
                Sign in
              </Link>
              <span className="font-mono-ph text-xs text-[var(--ph-muted)] ml-2">
                demo: admin@placeholder.in / admin123
              </span>
            </div>
          </div>

          <div className="lg:col-span-5 relative min-h-[360px]">
            <img
              src="https://images.unsplash.com/photo-1710582308582-55cc0c461c4e?crop=entropy&cs=srgb&fm=jpg&q=85"
              alt="Mumbai skyline"
              className="w-full h-full object-cover absolute inset-0 grayscale-[20%]"
            />
            <div className="absolute inset-0 bg-white/15" />
            <div className="absolute bottom-0 left-0 right-0 p-6 backdrop-blur-sm bg-white/70 border-t border-[var(--ph-line)]">
              <div className="tiny-caps text-[var(--ph-muted)]">Live tracking</div>
              <div className="font-display text-2xl font-bold mt-1">168+ active projects · 6 metros</div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats strip */}
      <section className="border-b border-[var(--ph-line)] bg-[var(--ph-bg-2)]">
        <div className="max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4">
          {[
            { k: "168+", v: "Projects tracked" },
            { k: "360+", v: "Sale & rent comps" },
            { k: "4", v: "Listed REITs modelled" },
            { k: "6", v: "Top metros · Tier-1" },
          ].map((s) => (
            <div key={s.v} className="px-6 py-8 border-r last:border-r-0 border-[var(--ph-line)]">
              <div className="font-display text-3xl lg:text-4xl font-bold tracking-tight">{s.k}</div>
              <div className="tiny-caps text-[var(--ph-muted)] mt-2">{s.v}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Three pillars */}
      <section className="max-w-7xl mx-auto px-6 lg:px-10 py-20">
        <div className="tiny-caps text-[var(--ph-muted)]">Phase 1 — what you get today</div>
        <h2 className="font-display text-3xl lg:text-4xl font-bold mt-3 tracking-tight max-w-3xl">
          Three connected products. One intelligence layer.
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 mt-12 border-l border-t border-[var(--ph-line)]">
          {[
            {
              icon: Map,
              title: "Developments Map",
              body: "Every metro line, airport, highway, residential tower & SEZ in your sub-market — geocoded, status-tagged, and filterable.",
            },
            {
              icon: Database,
              title: "Sale & Rent Comps",
              body: "Asking vs. sold prices, building age, land size, owner — a spreadsheet that's actually trustworthy.",
            },
            {
              icon: Calculator,
              title: "REIT-anchored WACC",
              body: "Plug in your debt stack, anchor your cost of equity to a listed Indian REIT, and get a defensible discount rate.",
            },
          ].map(({ icon: Icon, title, body }) => (
            <div key={title} className="border-r border-b border-[var(--ph-line)] p-8 hover:bg-[var(--ph-bg-2)] transition-colors">
              <Icon size={22} strokeWidth={1.5} />
              <div className="font-display font-bold text-xl mt-6">{title}</div>
              <p className="text-sm text-[var(--ph-ink-2)] mt-3 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-[var(--ph-line)]">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 py-8 flex flex-wrap justify-between items-center gap-4">
          <div className="font-mono-ph text-xs text-[var(--ph-muted)]">
            © PlaceHolder · Internal preview · v0.1
          </div>
          <div className="font-mono-ph text-xs text-[var(--ph-muted)]">
            Demo data only · Real data sources arrive in Phase 2.
          </div>
        </div>
      </footer>
    </div>
  );
}
