# PH7 Implementation Plan (Broker Integration)

Branch: `feature/ph7-broker-integration`  
Generated: 2026-03-16 (IST)

## 1) Docs Inspected First (Primary References)

- `docs/SigmaLab_PRD.md`
- `docs/PH2_Review_Report.md`
- `docs/PH3_Review_Report.md`
- `docs/PH4_Review_Report.md`
- `docs/PH4_Optimization_Readiness_Report.md`
- `docs/PH5_Implementation_Report.md`
- `docs/PH6_Implementation_Report.md`
- `docs/PH8_Implementation_Report.md`
- `README.md`

## 2) Relevant Code Inspected First

Backend:

- Settings/env: `backend/app/core/settings.py`
- Existing Kite client creation (env-only): `backend/app/services/kite_provider.py`
- Instrument sync uses Kite client: `backend/app/api/routes/instruments.py`, `backend/app/services/instruments.py`
- MarketDataService uses Kite client: `backend/app/services/market_data.py`
- Existing broker persistence model: `backend/app/models/orm.py` (`BrokerConnection` table exists)
- API router: `backend/app/api/router.py`

Frontend:

- Current Settings UX (truthful placeholder): `frontend/src/pages/SettingsPage.tsx`
- Frontend API client/types: `frontend/src/app/api/client.ts`, `frontend/src/app/api/types.ts`
- PH6 shell: `frontend/src/app/App.tsx`

## 3) PH7 Scope Derived From PRD + Current State

PH7 goal: make SigmaLab feel operationally connected to Zerodha/Kite for research readiness, with a SigmaTrader-like settings experience, without implementing trading/execution.

In scope:

- Persist broker configuration and connection status (DB-backed)
- Masked credential display (never return secrets)
- “Test connection” action and safe diagnostics
- Broker metadata snapshot (user/account identifiers where available)
- Update existing Kite integration points (instrument sync + historical data backfill) to use DB-stored credentials when configured
- Frontend Settings page upgrade (form + status + test button)

Out of scope:

- order placement / live execution
- portfolio/position tracking UI
- SigmaTrader handoff engine (only interoperability-ready metadata shapes)

## 4) Architecture / Storage Design

### 4.1 Primary persistence: `broker_connections`

Reuse existing ORM table:

- `broker_name` (Zerodha/Kite)
- `status` (disconnected/connected/error)
- `config_metadata` (safe, non-secret, user-displayable)
- `encrypted_secrets` (encrypted at rest; never returned to UI)
- `last_connected_at`, `last_verified_at`

We will enforce one row per broker provider by adding a uniqueness constraint on `broker_name`.

### 4.2 Secrets encryption

Requirement: do not store secrets in plaintext; never expose them over API.

Approach:

- Add `SIGMALAB_ENCRYPTION_KEY` (Fernet key) in backend settings.
- Encrypt `api_key`, `api_secret`, `access_token` into `encrypted_secrets`.
- Store only masked values and timestamps in `config_metadata`:
  - `api_key_masked`, `access_token_masked`
  - `configured` boolean
  - `last_test_status`, `last_test_message`
  - optional `profile` snapshot fields (e.g. `user_id`, `user_name`)

Behavior when encryption key is not configured:

- Read-only status endpoints still work.
- Attempts to save/update secrets return a clear error instructing to set `SIGMALAB_ENCRYPTION_KEY`.

## 5) Backend APIs (PH7)

Add a new settings router:

- `GET /settings/broker/kite`
  - returns display-safe broker connection state and masked config info
- `POST /settings/broker/kite`
  - accepts credentials and saves them encrypted; updates masked metadata
- `POST /settings/broker/kite/test`
  - attempts a safe Kite API call (e.g. `profile()`), updates status + metadata; returns safe diagnostics
- `POST /settings/broker/kite/clear-session` (optional but useful)
  - clears access_token only (keeps api_key/api_secret)

All responses are secret-safe by construction.

## 6) Update Existing Kite Usage (PH2/PH4 flows)

Currently Kite usage is env-only via `make_kite_client(settings)`.

PH7 will implement a DB-aware provider:

- prefer DB-stored credentials when configured
- fall back to env vars (for non-UI deployments)

Update call sites:

- `POST /instruments/sync` should use DB-stored Kite credentials when available
- MarketDataService backfill should use DB-stored Kite credentials when available

## 7) Frontend Settings UX (PH7)

Upgrade the existing Settings page to a SigmaTrader-like “Broker” section:

- status card:
  - not configured / configured but untested / test passed / test failed
  - last tested timestamp
- configuration form:
  - api_key (text)
  - api_secret (password)
  - access_token (password)
  - show masked values when already configured
  - update/rotate creds
- actions:
  - Save
  - Test connection
  - Clear session token (optional)
- broker metadata display:
  - `user_id`, `user_name` when available

UX rules:

- never display secrets
- show clear error messages without leaking secrets

## 8) Testing Plan

Backend unit tests:

- encryption/masking functions
- broker settings save/update does not leak secrets
- test endpoint uses a mockable adapter:
  - success
  - auth failure
  - network failure
- ensure logs/errors do not include secrets (basic assertions)

Backend integration tests (marked `integration`):

- create broker connection row in DB
- verify endpoints persist masked metadata and encrypted payload

Frontend tests (Vitest/RTL):

- Settings page renders broker section
- masked display behavior
- test connection flow states

## 9) Deliverables

- `docs/PH7_Implementation_Plan.md` (this doc)
- DB migration for broker_connections uniqueness
- Backend broker settings service + endpoints
- Frontend Settings page integration
- Tests + test results
- `docs/PH7_Implementation_Report.md`

