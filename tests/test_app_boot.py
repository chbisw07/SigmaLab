from __future__ import annotations

from app.core.settings import Settings
from app.main import create_app


def test_app_boots() -> None:
    app = create_app(Settings(env="test"))
    assert app.title == "SigmaLab API"

