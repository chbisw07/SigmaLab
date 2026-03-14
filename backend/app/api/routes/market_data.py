from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_app_settings, get_db_session
from app.core.settings import Settings
from app.services.market_data import make_market_data_service
from app.services.repos.instruments import InstrumentRepository

from data.timeframe import Timeframe

router = APIRouter()


@router.get("/candles")
def get_candles(
    instrument_id: uuid.UUID,
    timeframe: str = Query(..., description="Examples: 15m, 45m, 2h, 1D"),
    start: datetime = Query(...),
    end: datetime = Query(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
):
    try:
        tf = Timeframe.parse(timeframe)
        svc = make_market_data_service(settings, repo=InstrumentRepository(session))
        df = svc.get_candles(instrument_id=instrument_id, timeframe=tf, start=start, end=end)
        return {"status": "ok", "candles": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

