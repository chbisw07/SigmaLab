from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.instruments import router as instruments_router
from app.api.routes.market_data import router as market_data_router
from app.api.routes.strategies import router as strategies_router
from app.api.routes.watchlists import router as watchlists_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["system"])
api_router.include_router(instruments_router, prefix="/instruments", tags=["instruments"])
api_router.include_router(market_data_router, prefix="/market-data", tags=["market-data"])
api_router.include_router(watchlists_router, prefix="/watchlists", tags=["watchlists"])
api_router.include_router(strategies_router, prefix="/strategies", tags=["strategies"])
