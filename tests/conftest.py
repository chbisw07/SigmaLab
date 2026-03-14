from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    # Make `backend/` importable so tests can `import app...` without requiring
    # an editable install.
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    sys.path.insert(0, str(backend_dir))

