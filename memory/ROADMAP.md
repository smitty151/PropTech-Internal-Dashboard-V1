# PlaceHolder PropTech — Strategic Enhancement Roadmap
*Author: handoff from E1, 2026-02-XX. Phase 1, 2.1, 2.2, 2.3, 2.3.1 are built. This document scopes Phase 2.4 → 3.x.*

---

## 0 · Where we are today (the 3 built functions)

| Surface | What works | Live data |
|---|---|---|
| **Developments DB** | 193 projects, sovereign + private, map + table, source-attributed | NHAI/MoRTH ✓, Sub-Registrar partial, seeded mock for retail/comm |
| **Comps DB** | 374 sale + rent comps with confidence badges (VERIFIED vs SEED) | Maharashtra IGR + Delhi DORIS samples ✓, rest mock |
| **Valuation Memo** | One-click PDF, REIT-anchored WACC, all sources cited | Live; uses verified subset when "Verified only" is on |

**Gap vs. CoStar** (and Liases Foras / Reonomy / Cherre / Compstak / RCA): we have the *spine* of a valuation DB, but lack **depth of data** (leases, tenants, RERA project tracking, ownership graph) and **depth of analytics** (DCF, sensitivity, forecasting, comparable AI search). The memo is "indicative" — for it to be **defensible** at IC level, it needs adjusters (age, floor, age, view, amenities), multiple methods (income + cost), and sensitivity tables.

---

## 1 · The 4 themes to grow into a real advisory tool

```
DATA DEPTH ──────────►  MORE SOURCES, MORE FIELDS, MORE OBJECTS
ANALYTICS DEPTH ─────►  DCF, RESIDUAL LAND, SENSITIVITY, AI SEARCH
PRODUCT DEPTH ───────►  WATCHLISTS, DEAL ROOMS, ALERTS, COLLAB
COMMERCIAL DEPTH ────►  MULTI-TENANT, RBAC, BILLING, API ACCESS
```

---

## 2 · Phase 2.4 — Data Depth (the moat)

### 2.4.1 — New data sources to wire in (prioritised)

| # | Source | What it unlocks | Effort | Legal/ToS |
|---|---|---|---|---|
| 1 | **RERA portals (state-by-state)** | Live project status, escrow %, complaints, completion certificates | M | Public; mandatory disclosure |
| 2 | **MCA / ROC filings** | Ownership graph (which SPV owns which building), developer credit health | M | Public via MCA21 |
| 3 | **SEBI REIT quarterly filings** | NAV, LTV, NOI, WALE for listed REITs (4 → live) | S | Public |
| 4 | **RBI House Price Index + NHB Residex** | City-level index for trend overlays | S | Public CSV |
| 5 | **MoSPI / Census 2021** | Demographics, household income, occupation mix per ward | S | Public |
| 6 | **BSE/NSE listed-developer filings** | DLF, Godrej, Prestige, Brigade etc. — project pipelines from annual reports | M | Public |
| 7 | **MoHUA Smart Cities + AMRUT** | Sovereign urban infra commitments | S | Public CSV |
| 8 | **Power DISCOM consumption data** | Vacancy proxy (offices with high power = occupied) | L | Per state, RTI route |
| 9 | **IBBI / NCLT** | Distressed-asset pipeline (Stressed Asset Tracker) | M | Public |
| 10 | **Property tax records (municipal)** | Authoritative ownership + assessed value | L | Per-city portal scrape |
| 11 | **Mobile-footfall vendors** (Locale.ai, Near, Quadrant) | Retail/hospitality demand validation | L | Paid licence |
| 12 | **Compstak-style crowdsourced lease comps** | The Costar killer differentiator in India | L | Build crowd-sourcing UX + dedupe |

### 2.4.2 — New collections (Mongo schemas to add)

```
leases          { lease_id, building_id, tenant_id, start, end, area_sqft,
                  rent_psf_pm, escalation_pct, lock_in_yrs, security_deposit,
                  redacted_party (T/F), source }
tenants         { name, industry, parent_co, employee_count_est, occupies[
                  { building_id, area, since } ] }
buildings       { name, address, grade (A/A+/B/C), year_built, total_sqft,
                  floors, certifications [LEED, IGBC, …], vacancy_pct }
rera_projects   { rera_no, state, status, escrow_pct, complaints,
                  expected_completion, actual_completion, delays_months }
developers      { name, listed (T/F), credit_rating, delivery_track_record,
                  project_count, on_time_pct }
macros          { city, year_quarter, gdp_growth, employment_growth,
                  population, household_income_median, hpi, residex }
ownership_graph { entity, type (SPV/JV/Trust), parent, ubo, properties [] }
watchlists      { user_id, name, query_json, created_at, last_notified }
deals           { user_id, name, stage, properties [], target_close,
                  ic_date, notes [], assignees [], status }
valuation_models{ deal_id, method (sales/income/cost/residual),
                  assumptions, output, version, created_at }
alerts          { user_id, type, payload, sent_at, read_at }
api_keys        { user_id, key_hash, scopes, last_used, expires }
billing         { user_id, tier (FREE/PRO/ENT), seats, mrr, status,
                  stripe_subscription_id }
```

### 2.4.3 — New backend endpoints

```
GET    /api/leases?building_id=&tenant=&date_range=
GET    /api/tenants/{id}
GET    /api/buildings/{id}                  ← unified building object
GET    /api/buildings/{id}/comps            ← all comps for one building
GET    /api/buildings/{id}/leases
GET    /api/rera/projects?state=&status=
GET    /api/developers/{id}/scorecard       ← credit health + delivery record
GET    /api/macros?city=&from=&to=
GET    /api/ownership/{entity}              ← BFS through ownership graph
POST   /api/comps/similar                   ← AI: subject -> N similar comps
GET    /api/cap-rates?city=&asset_class=    ← median + IQR by submarket
POST   /api/valuation/dcf                   ← income method
POST   /api/valuation/residual-land
POST   /api/valuation/sensitivity           ← cap-rate ± 50bps matrix
GET    /api/watchlist
POST   /api/watchlist
GET    /api/deals  ← deal pipeline
POST   /api/deals
GET    /api/alerts
GET    /api/admin/audit-logs?action=&user_id=&from=&to=  ← we WRITE these
                                                          today but no UI
POST   /api/export/excel
POST   /api/export/powerbi-link
```

---

## 3 · Phase 2.5 — Analytics Depth (defensible memos)

### 3.1 — Multi-method valuation engine
Today: sales-comparison only (avg ₹/sqft × size). Add:

| Method | Inputs | When to use |
|---|---|---|
| **Sales Comparison (adjusted)** | comps + age/floor/view/amenity adjusters | Apartments, villas |
| **Income (Direct Cap)** | NOI ÷ cap rate (from comparable REIT/comp set) | Stabilised office, retail, hospitality |
| **Income (DCF)** | 10-yr NOI projection, exit cap, WACC discount | Pre-leased, development-stage assets |
| **Residual Land Value** | GDV − dev cost − dev profit − finance cost | Land parcels, redevelopment |
| **Cost Approach** | Replacement cost + land + depreciation | Specialised assets (hospitals, schools) |

Each method → a confidence score → memo shows **valuation range** not a single number.

### 3.2 — Sensitivity & scenario tables
- Cap rate ±25/50/75 bps
- Rent growth ±2/5%
- WACC ±100/200 bps
- 3 × 3 matrix in the PDF + interactive on UI.

### 3.3 — Cap-rate intelligence
- Pre-computed table of **median cap rate × asset class × submarket × quarter** (from comps + REIT data).
- Auto-suggested cap rate in Calculator with confidence band.

### 3.4 — Comp similarity AI
- "Find me 10 most-similar comps to this subject" — uses size, age, submarket, asset class, transaction date weighting.
- Powered by Claude Sonnet 4.6 or local embeddings on comp metadata (Emergent LLM key works for Claude text + GPT/Gemini, vendor-neutral).

### 3.5 — Forecasting overlay
- Supply pipeline (developments coming online next 24 months) vs absorption rate → submarket vacancy & rent forecast.
- 12-quarter forward HPI / Residex projection per city.

---

## 4 · Phase 2.6 — Product Depth (sticky workflows)

| Feature | Why | Effort |
|---|---|---|
| **Watchlists & saved searches** | Analysts come back daily; reduces re-typing | S |
| **Deal pipeline / deal rooms** | Each deal = workspace with attached comps, memos, notes, team | M |
| **Side-by-side compare** (2-5 properties) | Standard analyst workflow | S |
| **AI assistant** ("show me Grade-A office comps near HITEC City sold above ₹15K/sqft in last 12 mo") | Conversational query layer; lowers learning curve | M |
| **Email digests** (weekly/monthly) | Re-engagement loop | S |
| **Alerts** (e.g. "new comp in my submarket above ₹X/sqft") | Real-time value to subscribers | M |
| **Inline memo annotations** (Google-docs style) | Collaboration; trail of analyst thinking | M |
| **Client-branded memos** (logo upload + colour theme) | Premium-tier feature; consultants love this | S |
| **Mobile-responsive** | Currently desktop-first; site visits are mobile | M |
| **Dark mode** | Cosmetic but expected | S |
| **Keyboard shortcuts** | Power-user retention | S |
| **Admin audit-log viewer** | We WRITE audit logs (Task 4) but there's no UI to read them — compliance demand | S |
| **Bulk export** (Excel/CSV/PowerBI live link) | Enterprise table-stakes | M |
| **PDF memo versioning** | Compare v1 vs v2 of the same deal | S |

---

## 5 · Phase 2.7 — Commercial Depth (the business model)

### 5.1 — Multi-tenancy & RBAC
Today: single-tenant, admin + user role. Add:
- **Organisation** entity (every user belongs to one)
- **Org-scoped private data** (a firm's proprietary comps stay private to them)
- **Roles**: admin, partner, analyst, viewer
- **Org-level subscriptions** (Stripe integration via integration_playbook_expert_v2)

### 5.2 — Tier matrix (illustrative)

| Tier | Comps DB | Developments | Memos/mo | API | Seats | ₹/mo |
|---|---|---|---|---|---|---|
| **Free** | 10 reads/day | View only | 1 | — | 1 | 0 |
| **Pro** | unlimited | unlimited | 25 | — | 3 | 4,999 |
| **Team** | + bulk export | + alerts | 100 | — | 10 | 14,999 |
| **Enterprise** | + private comps | + API access | unlimited | 100k req/mo | unlimited | custom |

### 5.3 — Public API for B2B
- API keys, scopes, usage metering
- Rate-limit by key (slowapi already supports this — extend key_func)
- Audit-log every API call (already structured via Task 4)
- Docs site (mintlify / docusaurus / built-in `/docs` from FastAPI)

### 5.4 — Compliance & trust
- Audit-log viewer for admins (currently we write to `audit_logs`, no UI yet)
- Data residency: confirm Mongo is in-India region
- DPDP Act 2023 compliance: consent capture, deletion endpoint, DPO contact
- SOC-2 readiness (Phase 3)

---

## 6 · Inspiration map — what to borrow from whom

| Company | The 1 idea worth stealing |
|---|---|
| **CoStar** | Property Reports — 50-page deep-dives per building. Premium PDF that justifies the seat price. |
| **CoStar Market Analytics** | Forward-looking supply/demand forecasts per submarket. |
| **CoStar Risk Analytics** | Dynamic cap-rate forecasts with confidence bands. |
| **Reonomy** | Owner contact intelligence (UBO of an SPV). |
| **Compstak** | Crowdsourced lease comps with redacted-party model. |
| **Cherre** | Customer data lake (let Pro clients pipe their Yardi/MRI in). |
| **RCA (MSCI)** | Global transaction database with normalised cap rates across countries. |
| **VTS / Hightower** | Leasing CRM workflow (occupier vs landlord pipelines). |
| **Liases Foras** (India) | Quarterly market reports — credibility-by-publication. |
| **Anarock / JLL India** | Branded research notes as a lead magnet. |
| **Yardi / Argus** | Enterprise valuation engine — full DCF with line-item assumptions. |
| **PropEquity** (India) | Real-time RERA project tracking. |
| **99acres / Magicbricks** | Consumer-side listings → backfill of asking-price comps (scrape with care for ToS). |
| **Square Yards** | India-specific transaction registry with bank loan attach-rates. |
| **JLL Property Predict** | AI-powered valuation for residential apartments. |

---

## 7 · Suggested next-12-week plan

```
Weeks 1-2   |  Phase 2.4.1  → RERA + REIT filings + MCA wired in
Weeks 3-4   |  Phase 2.4.2  → New collections (leases, tenants, buildings, rera, developers, macros)
Weeks 5-6   |  Phase 2.5.1  → Multi-method valuation engine (DCF + residual land)
Weeks 7-8   |  Phase 2.5.2  → Sensitivity tables in memo PDF + cap-rate intelligence
Weeks 9-10  |  Phase 2.6    → Watchlists, deal rooms, alerts, admin audit viewer
Weeks 11-12 |  Phase 2.7    → Multi-tenancy + Stripe + API keys (commercial-ready)
```

Pick one stream to obsess on per fortnight. **Recommendation: weeks 1-4 first (data depth)** — it's the moat and everything else depends on it.

---

## 8 · Known minor cleanups (carry-forward backlog)

- [ ] `Calculator.js`: stable `key` prop on tranche list + remove `<span>` from inside `<option>` (invalid HTML; React warning).
- [ ] `LIMITER_ENABLED=true` in `/app/backend/.env` before any production deploy (currently `false` for test convenience; rate-limit code itself is verified working).
- [ ] PRD.md was stale on Phase 2.3/2.3.1 entries; document the email-verification flow there.
- [ ] Admin "audit logs" UI page (route `/app/audit`) — we write logs but no read view yet.
- [ ] Memo PDF list endpoint caps at 50 — fine for now, pagination needed once a user generates >50.
