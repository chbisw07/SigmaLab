from __future__ import annotations

import os
import sys
from pathlib import Path


# Ensure local `.env` does not break unit test collection when it contains
# incomplete placeholders. Environment vars take precedence over dotenv.
os.environ.setdefault(
    "SIGMALAB_DATABASE_URL",
    "postgresql+psycopg://sigmalab:sigmalab@localhost:5432/sigmalab",
)
os.environ.setdefault("SIGMALAB_ENV", "test")


def pytest_configure() -> None:
    # Make `backend/` importable so tests can `import app...` without requiring
    # an editable install.
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    sys.path.insert(0, str(backend_dir))
