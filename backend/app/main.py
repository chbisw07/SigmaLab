from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    # Allow a separate local dev frontend to call the API.
    # In prod, set SIGMALAB_CORS_ORIGINS explicitly.
    origins = list(settings.cors_origins)
    if not origins and settings.env in ("local", "dev"):
        origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router)

    @app.get("/", tags=["system"])
    def root() -> dict[str, str]:
        return {"name": "sigmalab", "status": "ok"}

    return app


app = create_app()
