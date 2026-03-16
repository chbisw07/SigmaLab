# PH7 Implementation Report (Broker Integration)

Branch: `feature/ph7-broker-integration`  
Generated: 2026-03-16 (Asia/Kolkata)

## Purpose

PH7 implements **broker integration readiness** for SigmaLab, focused on:

- Zerodha/Kite credential management (research data access)
- safe connection testing
- broker metadata snapshot for continuity
- SigmaTrader-aligned settings UX patterns

PH7 explicitly does **not** implement:

- order placement
- live trading/execution UI
- positions/holdings tracking

SigmaLab remains a **research workbench**; SigmaTrader remains the execution product.

## Docs And Code Inspected First

Docs:

- `docs/SigmaLab_PRD.md`
- `docs/PH2_Review_Report.md`
- `docs/PH3_Review_Report.md`
- `docs/PH4_Review_Report.md`
- `docs/PH4_Optimization_Readiness_Report.md`
- `docs/PH5_Implementation_Report.md`
- `docs/PH6_Implementation_Report.md`
- `docs/PH8_Implementation_Report.md`
- `README.md`

Backend code:

- `backend/app/services/kite_provider.py`
- `backend/app/api/routes/instruments.py`
- `backend/app/services/market_data.py`
- existing ORM schema in `backend/app/models/orm.py`

Frontend code:

- `frontend/src/pages/SettingsPage.tsx`
- API client/types in `frontend/src/app/api/*`

## Implemented Scope

### 1. Secure Broker Settings Persistence (DB-backed)

Reused existing `BrokerConnection` table as the persistent settings record for broker connections.

Security design:

- Credentials are stored **encrypted-at-rest** in PostgreSQL using **Fernet** via `cryptography`.
- Encryption key is provided via `SIGMALAB_ENCRYPTION_KEY` (backend environment).
- API responses never return raw secrets; only masked values are returned.

### 2. Zerodha/Kite Settings Backend Service

Added a small, mockable service layer:

- Save/merge Kite credentials (api_key, api_secret, access_token)
- Clear session (drops access_token, keeps api_key/api_secret)
- Test connection using Kite `profile()` call
- Persist safe broker profile snapshot (user_id, user_name, etc.)
- Persist status and timestamps

### 3. PH7 Settings API Endpoints

Added the following endpoints under `/settings`:

- `GET /settings/broker/kite` (public, masked state)
- `POST /settings/broker/kite` (save/update credentials; encrypted-at-rest)
- `POST /settings/broker/kite/test` (connection test via `profile()`)
- `POST /settings/broker/kite/clear-session`

### 4. Wiring Existing Data Workflows To Use DB Credentials

Updated Kite client creation to prefer DB-stored encrypted credentials when a DB session is available:

- Instrument sync (`POST /instruments/sync`)
- Market data backfill (MarketDataService missing-range fetch path)

Fallback behavior remains:

- If DB creds are not configured, SigmaLab falls back to env vars:
  - `SIGMALAB_KITE_API_KEY`
  - `SIGMALAB_KITE_ACCESS_TOKEN`

### 5. Settings UI (Frontend)

Enhanced Settings page with a dedicated Zerodha/Kite section:

- show current broker status (`disconnected` / `connected` / `error`)
- show masked configured values
- form inputs for api_key, api_secret, access_token
- actions:
  - Save
  - Test connection
  - Clear session

### 6. Documentation

- `.env.example` now includes `SIGMALAB_ENCRYPTION_KEY` guidance.
- Added Kite access-token helper doc:
  - `docs/HOWTO_kite_access_token.md`
- Updated README with PH7 endpoints and notes.

## Files Added / Updated

Backend:

- `backend/app/core/secrets.py`
- `backend/app/core/settings.py`
- `backend/app/models/orm.py`
- `backend/app/services/repos/broker_connections.py`
- `backend/app/services/broker_settings.py`
- `backend/app/services/kite_provider.py`
- `backend/app/api/routes/settings.py`
- `backend/app/api/router.py`
- `backend/app/api/routes/instruments.py`
- `backend/app/services/market_data.py`
- `backend/alembic/versions/1c7d5a2b8c2e_ph7_broker_connections_unique_broker_name.py`

Frontend:

- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/app/api/client.ts`
- `frontend/src/app/api/types.ts`
- `frontend/src/styles.css`
- `frontend/src/__tests__/settings_kite_section.test.tsx`

Tests:

- `tests/test_secrets.py`
- `tests/test_broker_settings_service.py`
- `tests/test_ph7_broker_settings_integration.py` (marked `integration`)

Docs:

- `.env.example`
- `README.md`
- `docs/HOWTO_kite_access_token.md`

## Database / Migrations

Migration added:

- `1c7d5a2b8c2e_ph7_broker_connections_unique_broker_name.py`

Schema change:

- Unique constraint on `broker_connections.broker_name` to enforce **one row per broker provider**.

## Security / Secrets Handling

Rules enforced:

- Raw credentials are never returned to the frontend.
- Only masked values are surfaced (`****1234` style).
- DB persistence requires `SIGMALAB_ENCRYPTION_KEY`.

Operational note:

- If `SIGMALAB_ENCRYPTION_KEY` changes, previously stored secrets cannot be decrypted. Use the Settings UI to re-save credentials (or clear/reset the row).

## How To Use (Manual Validation)

1. Set encryption key in backend `.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set:

```text
SIGMALAB_ENCRYPTION_KEY=<PRINTED_KEY>
```

2. Start backend and frontend.

3. Go to `Settings` and:

- paste api_key + api_secret + access_token
- Save
- Test connection (should flip status to `connected` if access_token is valid)

4. Confirm you can:

- `POST /instruments/sync`
- run `MarketDataService` backfills (e.g., via backtests) without env-based creds

Access token helper:

- [docs/HOWTO_kite_access_token.md](docs/HOWTO_kite_access_token.md)

## Tests

Backend unit tests:

```bash
.venv/bin/pytest
```

Integration tests (requires Postgres test DB):

```bash
SIGMALAB_TEST_DATABASE_URL="postgresql+psycopg://sigmalab:sigmalab@localhost:5432/sigmalab" \
  .venv/bin/pytest -m integration -v
```

Frontend tests:

```bash
cd frontend
npm test
```

## Known Limitations / Deferred

- No UI flow for generating `access_token` itself (still uses helper script; full request_token auth flow remains out-of-scope).
- No multi-broker abstraction beyond Zerodha/Kite (kept intentionally minimal for v1).
- No SigmaTrader export/handoff workflow (PH7 is readiness only).

## Review Checklist

- Settings UI shows masked values only; no secrets appear in network responses.
- Save/test/clear-session actions behave as expected.
- `SIGMALAB_ENCRYPTION_KEY` required for DB credential storage; errors are actionable.
- Instrument sync and market-data backfill work with DB-stored creds when configured.
- Unit tests pass; integration tests run when `SIGMALAB_TEST_DATABASE_URL` is set.

