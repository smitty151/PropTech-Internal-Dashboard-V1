import { NavLink, Outlet, Link } from "react-router-dom";
import { Building2, Map, Database, Calculator, LogOut, LayoutGrid, Cable, FileDown } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const navItems = [
  { to: "/app", icon: LayoutGrid, label: "Overview", testId: "nav-overview", end: true },
  { to: "/app/developments", icon: Map, label: "Developments", testId: "nav-developments" },
  { to: "/app/comps", icon: Database, label: "Comps DB", testId: "nav-comps" },
  { to: "/app/calculator", icon: Calculator, label: "Cost of Capital", testId: "nav-calculator" },
  { to: "/app/memo", icon: FileDown, label: "Valuation Memo", testId: "nav-memo" },
  { to: "/app/data-sources", icon: Cable, label: "Data Sources", testId: "nav-data-sources" },
];

export default function AppShell() {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-[var(--ph-line)] bg-white">
        <div className="flex items-center justify-between px-6 h-14">
          <Link to="/app" className="flex items-center gap-2" data-testid="brand-link">
            <Building2 size={18} strokeWidth={1.5} />
            <span className="font-display text-lg font-bold tracking-tight">PlaceHolder</span>
            <span className="tiny-caps text-[var(--ph-muted)] ml-2">India PropTech Intelligence</span>
          </Link>
          <div className="flex items-center gap-4">
            <div className="text-sm">
              <div className="font-medium" data-testid="user-name">{user?.name}</div>
              <div className="text-xs text-[var(--ph-muted)] font-mono-ph">{user?.email}</div>
            </div>
            <button
              data-testid="logout-btn"
              onClick={logout}
              className="btn-outline flex items-center gap-2 !py-1.5 !px-3 text-sm"
            >
              <LogOut size={14} /> Logout
            </button>
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        <aside className="w-56 border-r border-[var(--ph-line)] bg-[var(--ph-bg-2)]">
          <nav className="p-3 flex flex-col gap-1">
            {navItems.map(({ to, icon: Icon, label, testId, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                data-testid={testId}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 text-sm border border-transparent ${
                    isActive
                      ? "bg-[var(--ph-ink)] text-white"
                      : "text-[var(--ph-ink)] hover:bg-white hover:border-[var(--ph-line)]"
                  }`
                }
              >
                <Icon size={16} strokeWidth={1.5} />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="px-4 mt-4">
            <div className="tiny-caps text-[var(--ph-muted)] mb-2">Phase 1 build</div>
            <p className="text-xs text-[var(--ph-ink-2)] leading-relaxed">
              Data shown is seeded for demonstration. Phase 2 will plug in RERA, govt portals & real-time scrapers.
            </p>
          </div>
        </aside>

        <main className="flex-1 bg-white overflow-x-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
