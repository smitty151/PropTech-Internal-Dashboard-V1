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

## Backlog (Phase 2.5+)
**P0 — make data real**
- RERA API integration per state (residential)
- Govt portals scrapers (NHAI / MoCA / Railways / metro corporations) for infra projects
- MagicBricks / 99acres / Housing.com scrapers for comps (asking) + Sub-Registrar data (sold)
- Reuters / Yahoo for live REIT prices & yields

**P1 — analytics & advisory**
- Sub-market heatmaps (price growth, absorption, vacancy)
- Comparable-sales-driven valuation reports (PDF export)
- Saved searches, watchlists & email alerts
- Building-level pages (transaction history, ownership chain, photos)
- Cap rate calculator + DCF templates with sensitivity analysis

**P2 — monetisation**
- Subscription tiering (Starter / Pro / Enterprise) with Razorpay/Stripe
- API access for B2B customers
- Team workspaces & sharing
- Mobile app

## Known Limitations
- All numbers are seeded mock data; no live sources connected yet
- No payment / subscription flow
- No multi-tenant data scoping
