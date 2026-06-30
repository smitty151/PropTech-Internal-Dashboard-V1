# Handoff Prompt — Start of Phase 2.4

> Paste the block below into a fresh Emergent chat to continue PlaceHolder PropTech.
> Everything between `<<<` and `>>>` is the prompt; trim what you don't need.

---

```
<<<
Continuing PlaceHolder PropTech — India real estate intelligence platform.
The code lives on GitHub at https://github.com/smitty151/PropTech-Internal-Dashboard-V1.git
The repo is public. The architecture and current state are documented at
/app/memory/PRD.md, /app/memory/ROADMAP.md, and /app/memory/test_credentials.md.

STEP 1 — Restore the codebase:

  cd /app && rm -rf backend frontend memory && \
  git clone https://github.com/smitty151/PropTech-Internal-Dashboard-V1.git /tmp/ph && \
  cp -r /tmp/ph/backend /tmp/ph/frontend /tmp/ph/memory /app/ && \
  cd /app/backend && pip install -r requirements.txt && \
  cd /app/frontend && yarn install && \
  sudo supervisorctl restart backend frontend

STEP 2 — Create /app/backend/.env with these values (replace the FRONTEND_URL
with this preview's REACT_APP_BACKEND_URL):

  MONGO_URL="mongodb://localhost:27017"
  DB_NAME="placeholder_proptech"
  CORS_ORIGINS="<paste this preview's REACT_APP_BACKEND_URL>,http://localhost:3000"
  JWT_SECRET="b8f3a17c4e2d9f7a1c5b8e3a9d2f7c1b4e6a8d3f9c7b2e5a8d1f4c7b9e2a5d8f"
  ADMIN_EMAIL="admin@placeholder.in"
  ADMIN_PASSWORD="admin123"
  RESEND_API_KEY="re_52G9qT3q_27FjvQMbzybgppNHGbnERRGv"
  SENDER_EMAIL="onboarding@resend.dev"
  FRONTEND_URL="<paste this preview's REACT_APP_BACKEND_URL>"
  LIMITER_ENABLED="true"

  (Note: LIMITER_ENABLED is "true" for production-realistic behaviour. If you
  need the test suite to run without throttling, flip it to "false" temporarily.)

STEP 3 — Read the context files before doing anything else:
  - /app/memory/PRD.md         (architecture, phases built, backlog)
  - /app/memory/ROADMAP.md     (Phase 2.4 → 3.x strategic plan)
  - /app/memory/test_credentials.md  (admin login)

STEP 4 — Verify restore (stop and ask me if any check fails):
  - /app/backend/server.py mounts routers from /app/backend/routers/
  - /app/backend/models.py defines PyObjectId + BaseDocument + User/Memo/
    Development/Comp/Reit/DataSourceRun/AuditLog
  - /app/backend/core/{db,security,rate_limit,audit,email_utils}.py exist
  - /app/frontend/src/components/ErrorBoundary.jsx wraps the app
  - Login at admin@placeholder.in / admin123 works
  - Curl POST /api/valuation-memo returns a PDF (use cookie auth)

STEP 5 — Re-seed live data (Mongo will be empty on this new pod):
  Log in as admin → /app/data-sources → click Refresh on NHAI and
  Sub-Registrar so the 39 verified records repopulate.

────────────────────────────────────────────────────────────────────────
NEW WORK FOR THIS SESSION — Phase 2.4: Data Depth
────────────────────────────────────────────────────────────────────────

Build the data foundation that turns the platform from "indicative" to
"defensible." Pick ONE of the two tracks below — ask me which to start.

  TRACK A — RERA + Developer Scorecard
  ─────────────────────────────────────
  Goal: turn /app/developments from "list of projects" into
  "live project tracker with completion-risk score."

  Models to add (in /app/backend/models.py, following the existing
  BaseDocument + to_mongo/from_mongo pattern):
    • ReraProject  { rera_no, state, status, escrow_pct, complaints,
                     expected_completion, actual_completion,
                     delays_months, developer_id }
    • Developer    { name, listed, credit_rating, delivery_track_record,
                     project_count, on_time_pct }

  Endpoints (mount in routers/):
    • GET  /api/rera/projects?state=&status=&developer=
    • GET  /api/developers/{id}/scorecard

  Data source connectors (in /app/backend/data_sources/):
    • rera_data.py — scrape Maharashtra MahaRERA + Karnataka RERA + Telangana
      RERA list endpoints; normalise into the ReraProject model. Start with
      one state to validate the schema; add more states iteratively.
    • Add a refresh job under /api/data-sources/rera/refresh (require admin
      role) — patterned after /nhai/refresh.

  Frontend:
    • New page /app/rera with table + status filter + complaint counter
    • In /app/developments detail panel, show "RERA: <status, escrow %,
      delay months>" pulled from rera_projects joined on developer or
      project external_id.

  Audit log: record_audit("rera_refresh", payload={state, ingested})

  TRACK B — Lease comps + Tenant directory (the CoStar killer)
  ─────────────────────────────────────────────────────────────
  Goal: the first India-specific platform with structured lease comps.

  Models to add:
    • Building    { name, address, city, submarket, grade (A/A+/B/C),
                    year_built, total_sqft, floors, certifications [],
                    vacancy_pct, lat, lng }
    • Tenant      { name, industry, parent_co, employee_count_est }
    • Lease       { building_id, tenant_id, start, end, area_sqft,
                    rent_psf_pm, escalation_pct, lock_in_yrs,
                    security_deposit_months, redacted_party, source }

  Endpoints:
    • GET  /api/buildings  (with filters)
    • GET  /api/buildings/{id}  (composite: building + comps + leases)
    • GET  /api/buildings/{id}/leases
    • GET  /api/tenants/{id}
    • POST /api/leases (create — admin only initially; later open to
      crowd-sourced submission with redact flag)

  Frontend:
    • New page /app/buildings — search + map + grade badges
    • Building detail page with three tabs: Overview, Sale Comps, Lease Comps
    • Tenant directory page /app/tenants

────────────────────────────────────────────────────────────────────────
STANDING RULES (don't violate)
────────────────────────────────────────────────────────────────────────

1. All new collections MUST extend BaseDocument from /app/backend/models.py
   (PyObjectId + from_mongo + to_mongo). No raw dict spreads on inserts.
2. All new endpoints under /api prefix; mounted via APIRouter under
   /app/backend/routers/. Server.py stays thin.
3. All write/refresh endpoints MUST call core.audit.record_audit(action, ...)
   with action one of: login, logout, memo_generated, data_source_refresh,
   verification_email_sent, rera_refresh, lease_created, building_created,
   admin_action (and any new ones you introduce — document them).
4. Rate limits stay as-is: global 60/min/IP, /auth/* 5/min/IP,
   /valuation-memo 5/min/user. New data-mutation endpoints (POST /leases,
   POST /buildings, POST /rera refresh) should get a sensible @limiter.limit
   decorator (5-20/min depending on cost).
5. Frontend: continue using shadcn components from
   /app/frontend/src/components/ui/. Match the existing "Swiss / Control
   Room" aesthetic (off-white #F7F7F4, ink #0A0A0A, mono accents, sparse
   borders). Avoid AI-slop gradients. Use data-testid on every interactive.
6. Tests: after each new endpoint/page, call testing_agent_v3 with the
   regression suite + the new test file (pattern: /app/backend/tests/
   test_phase24_<track>.py).
7. PRD.md: append an "Implemented (Phase 2.4)" section as you ship.

────────────────────────────────────────────────────────────────────────
DECISIONS I NEED FROM YOU FIRST
────────────────────────────────────────────────────────────────────────

Use the ask_human tool to confirm before writing code:

  1. TRACK A (RERA + Developer Scorecard) or TRACK B (Buildings + Tenants
     + Lease Comps)? Recommend: A first (faster, builds trust); B second.
  2. For lease-comp ingestion (TRACK B), should we (a) seed a curated
     starter set from public REIT filings, or (b) build a crowdsourced
     submission form first (CompStak model)?
  3. Stripe — do we want to set up the billing scaffolding now (Pro tier
     paywalls Bulk Export + Alerts) or defer to Phase 2.7?
  4. Email digests / alerts — Resend (already configured) is fine; OK to
     reuse the same API key for transactional digests?

After you answer, I'll build, test (via testing_agent_v3), and finish.
>>>
```

---

## Why a fresh chat?

This conversation has gotten long. A new chat starts with a clean context
budget so I can think harder about the data modelling for Phase 2.4.
The PRD + ROADMAP + test_credentials in `/app/memory/` are the durable
contract — every future session reads those first.
