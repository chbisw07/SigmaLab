from __future__ import annotations

from fastapi import FastAPI

from app.api.router import api_router
from app.core.db import Database
from app.core.logging import configure_logging
from app.core.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(title="SigmaLab API", version="0.1.0")
    app.state.settings = settings
    app.state.database = Database.from_settings(settings)
    app.include_router(api_router)

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"name": "sigmalab", "status": "ok"}

    return app


app = create_app()
