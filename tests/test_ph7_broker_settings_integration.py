from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.settings import Settings
from app.main import create_app


def _test_db_url() -> str | None:
    return os.environ.get("SIGMALAB_TEST_DATABASE_URL")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _reset_public_schema(engine) -> None:  # type: ignore[no-untyped-def]
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.mark.integration
def test_ph7_kite_settings_save_get_clear_session_postgres() -> None:
    url = _test_db_url()
    if not url:
        pytest.skip("Set SIGMALAB_TEST_DATABASE_URL to run Postgres integration tests")

    engine = create_engine(url, future=True)
    _reset_public_schema(engine)

    env = os.environ.copy()
    env["SIGMALAB_DATABASE_URL"] = url
    env["SIGMALAB_ENV"] = "test"
    subprocess.run(
        [sys.executable, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"],
        cwd=str(_repo_root()),
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    key = Fernet.generate_key().decode("utf-8")
    app = create_app(Settings(env="test", database_url=url, encryption_key=key))
    client = TestClient(app)

    payload = {"api_key": "k1234", "api_secret": "s9999", "access_token": "t5555"}
    r = client.post("/settings/broker/kite", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()

    # Ensure secrets are not leaked in responses.
    s = r.text
    assert "k1234" not in s
    assert "s9999" not in s
    assert "t5555" not in s
    assert data["configured"] is True
    assert data["masked"]["api_key"].endswith("1234")

    g = client.get("/settings/broker/kite")
    assert g.status_code == 200, g.text
    state = g.json()
    assert state["configured"] is True
    assert "k1234" not in g.text

    c = client.post("/settings/broker/kite/clear-session", json={})
    assert c.status_code == 200, c.text
    cleared = c.json()
    assert cleared["metadata"]["has_access_token"] is False
    assert cleared["masked"]["access_token"] is None

