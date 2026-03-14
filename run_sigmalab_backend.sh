#!/usr/bin/env bash
set -euo pipefail

# SigmaLab PH1 runner:
# - activates .venv
# - starts PostgreSQL (systemd)
# - ensures DB/user exist (idempotent)
# - runs Alembic migrations
# - runs the backend (uvicorn)

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  # Export vars from .env if present.
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

SIGMALAB_DATABASE_URL="${SIGMALAB_DATABASE_URL:-postgresql+psycopg://sigmalab:sigmalab@localhost:5432/sigmalab}"
export SIGMALAB_DATABASE_URL

if [[ ! -d ".venv" ]]; then
  echo "Missing .venv. Create it first:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install --upgrade pip"
  echo "  .venv/bin/pip install -r requirements-dev.txt"
  exit 1
fi

# shellcheck disable=SC1091
source ".venv/bin/activate"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql not found. Install PostgreSQL client/server first:"
  echo "  sudo apt-get update"
  echo "  sudo apt-get install -y postgresql postgresql-contrib"
  exit 1
fi

if ! command -v pg_isready >/dev/null 2>&1; then
  echo "pg_isready not found. Install PostgreSQL first:"
  echo "  sudo apt-get install -y postgresql"
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl not found. This script expects a systemd-managed PostgreSQL service."
  exit 1
fi

echo "Starting PostgreSQL service (may prompt for sudo password)..."
sudo -v
sudo systemctl start postgresql

echo "Waiting for PostgreSQL to become ready..."
pg_isready

# Parse DB connection parts from SIGMALAB_DATABASE_URL.
read -r DB_USER DB_PASS DB_HOST DB_PORT DB_NAME < <(
  python - <<'PY'
import os
from urllib.parse import urlparse

url = os.environ.get("SIGMALAB_DATABASE_URL", "")
u = urlparse(url)

user = u.username or "sigmalab"
password = u.password or ""
host = u.hostname or "localhost"
port = str(u.port or 5432)
db = (u.path or "/sigmalab").lstrip("/") or "sigmalab"

print(f"{user} {password} {host} {port} {db}")
PY
)

echo "Ensuring role '$DB_USER' and database '$DB_NAME' exist..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -tAc "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}') THEN CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASS}'; END IF; END \$\$;"
sudo -u postgres psql -v ON_ERROR_STOP=1 -tAc "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname='${DB_NAME}') THEN CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}; END IF; END \$\$;"
sudo -u postgres psql -v ON_ERROR_STOP=1 -tAc "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

echo "Running Alembic migrations..."
alembic -c backend/alembic.ini upgrade head

echo "Starting SigmaLab backend on http://127.0.0.1:8000 ..."
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

