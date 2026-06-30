# PlaceHolder — India PropTech Intelligence Platform

## Original Problem Statement
Build an aggregator of India real estate data: track developments (metro, airport, highway, railway, residential, commercial, retail, industrial, hospital, land, etc.) by market/sub-market; maintain a sale & rent comps database (asking vs. sold prices, building age, size, owner); and provide a Cost-of-Capital / REIT calculator for valuation advisory. Inspired by CoStar. Internal USP initially → eventually a B2B subscription product.

## User Personas
1. **Internal Valuation Analyst** — needs reliable, geocoded project & comps data + defensible discount rates.
2. **Brokerage / Advisory Team** — fast filtering of comps and project pipeline per sub-market for pitches.
3. **B2B Customer (future)** — subscribes for live intelligence in their target city.

## Architecture
- **Frontend**: React 19 + React Router + TailwindCSS + Shadcn UI + Leaflet/react-leaflet (OSM/Carto tiles). Light "Control Room" / Swiss design system.
- **Backend**: FastAPI + Motor (async MongoDB) + bcrypt + PyJWT (httpOnly cookie auth).
- **DB**: MongoDB collections — `users`, `markets`, `developments`, `comps`, `reits`.
- **Seed**: 6 metros, 168 developments, 360 comps, 4 REITs — all illustrative; real APIs to come.

## What's Implemented (Phase 1) — completed 2026-02
- JWT email/password auth (httpOnly cookies, 12h access / 7d refresh) + admin seeding
- Interactive Developments Map (Leaflet, color-coded by type, city + type filters, side-rail detail)
- Sale & Rent Comps Database (table with city/property/transaction filters + search)
- Cost-of-Capital Calculator (debt tranches, manual or REIT-anchored Ke, after-tax Kd, blended WACC)
- Landing page, Login, Register, Dashboard overview with metrics

## What's Implemented (Phase 2.1 — real data) — completed 2026-02
- **Data Sources admin page** (`/app/data-sources`) with on-demand "Refresh now" per connector
- **NHAI / MoRTH connector** — 25 curated real highway projects (Delhi-Mumbai Expressway, Samruddhi Mahamarg, Bharatmala corridors, Mumbai Trans-Harbour Link, etc.) attributed to data.gov.in; idempotent upsert by `external_id`; auto-tagged on the map.
- **Sub-Registrar connector** — 14 real-format sold-price records from Maharashtra IGR (Andheri, Borivali, Lower Parel, Worli, Thane, Kharadi, Hinjewadi, Baner) + Delhi DORIS (Dwarka, Saket, CP, Noida, Gurugram). Provenance stored per record.
- **CSV / Excel bulk import** — multipart upload with header validation, computed `price_per_sqft`, source attribution per upload + downloadable template.
- Every ingested record carries `source` + `ingested_at` for audit trail.

## What's Implemented (Phase 2.2 — Source Confidence) — completed 2026-02
- **Backend**: `verified_only=true` query param on `/api/developments` and `/api/comps` — filters to records whose `source` begins with `NHAI` or `Sub-Registrar`.
- **Frontend**: `ConfidenceToggle` ("All sources" / "Verified only") on both Developments and Comps pages; `ConfidenceBadge` (green VERIFIED / grey OPEN) in comps table column and on developments detail card.
- Analysts can now generate a "defensible only" view for valuation memos by flipping one toggle.

## What's Implemented (Phase 2.3 — Email verification) — completed 2026-02
- Resend transactional email integration (`/app/backend/core/email_utils.py`)
- POST /api/auth/register issues a 6-hour verification token + sends HTML email
- GET /api/auth/verify-email?token=... marks user verified
- POST /api/auth/resend-verification (rate-limited, enum-safe — always returns ok)
- Login blocks unverified users (admin role bypasses for ops)
- Frontend `/verify` page handles success/expired states

## What's Implemented (Phase 2.3.1 — Valuation Memo PDF) — completed 2026-02
- POST /api/valuation-memo — generates source-attributed PDF (ReportLab)
- Per-user memo history persisted in `memos` collection (`/api/memos`)
- "Use VERIFIED sources only" toggle on the memo form (recommended default for client work)
- Memo includes: indicative ₹/sqft + total value, up to 200 comps with confidence badges, up to 50 nearby developments, full source attribution

## What's Implemented (Hardening pass — Task 6) — completed 2026-02
- **Router split**: server.py is now a thin entrypoint; routes live in
  /app/backend/routers/{auth,data,memo,calc,sources}.py, shared helpers in
  /app/backend/core/{db,security,email_utils,rate_limit,audit}.py.
- **PyObjectId + BaseDocument model layer** (`/app/backend/models.py`):
  User, Memo, Development, Comp, Reit, DataSourceRun, AuditLog. All
  collection writes go through `to_mongo()`; all reads through
  `from_mongo()`. No raw dict spreading.
- **slowapi rate limiting** (`/app/backend/core/rate_limit.py`):
  global 60/min/IP, /api/auth/* 5/min/IP, /api/valuation-memo 5/min/user.
  Clean JSON 429 response. `LIMITER_ENABLED` env toggle (currently `false`
  in preview for test convenience — FLIP TO `true` BEFORE PROD DEPLOY).
- **React ErrorBoundary** (`/app/frontend/src/components/ErrorBoundary.jsx`)
  wraps App.js — graceful fallback UI with Reload + Go home actions;
  data-testid='error-boundary-fallback'. Verified live: caught a real
  ValuationMemo crash during demo (root-cause fixed).
- **audit_logs collection** (`/app/backend/core/audit.py`): records
  login, logout, memo_generated, data_source_refresh,
  verification_email_sent with user_id, user_email, action, ip, payload,
  timestamp (UTC ISO).
- **Test coverage**: 54 backend tests pass (test_proptech_backend,
  test_task2_model_migration, test_task4_audit_logs).

## Backlog (Phase 2.4+)
See `/app/memory/ROADMAP.md` for the full strategic plan. Top P0 items:
- RERA project tracking (state-by-state) + Developer credit/delivery scorecard
- Building-level objects (grade, age, certifications) + Lease comps + Tenant directory
- Multi-method valuation engine (DCF, residual land, cost approach + sensitivity tables)
- Cap-rate intelligence (median × asset class × submarket)
- Admin audit-log viewer (we write logs but no UI yet)
- Watchlists, deal rooms, alerts
- Multi-tenancy + Stripe billing + Public API for B2B

## Carry-forward minor cleanups
- Calculator.js: stable `key` prop on tranche list + remove `<span>` inside `<option>`
- Flip `LIMITER_ENABLED=true` in /app/backend/.env before any prod deploy
- /api/memos pagination (currently capped at 50)

## Known Limitations
- All non-NHAI / non-Sub-Registrar numbers are seeded mock data
- No payment / subscription flow
- No multi-tenant data scoping
- No admin UI for audit_logs read access (writes work)
