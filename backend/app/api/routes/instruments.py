from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

from app.core.deps import get_app_settings, get_db_session
from app.core.settings import Settings
from app.models.schemas import InstrumentSchema
from app.services.instruments import InstrumentService
from app.services.kite_provider import make_kite_client
from app.services.repos.instruments import InstrumentRepository

router = APIRouter()


@router.post("/sync")
def sync_instruments(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
):
    try:
        kite = make_kite_client(settings)
        repo = InstrumentRepository(session)
        n = InstrumentService(kite=kite, repo=repo).sync_instruments()
        return {"status": "ok", "upserted": n}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=list[InstrumentSchema])
def list_instruments(
    q: str | None = Query(default=None, description="Search by symbol or name (substring match)"),
    exchange: str | None = Query(default=None, description="Example: NSE"),
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_db_session),
):
    repo = InstrumentRepository(session)
    if q:
        return repo.search(q=q, exchange=exchange, limit=limit)
    if exchange:
        return repo.search(q="", exchange=exchange, limit=limit)
    return repo.list(limit=limit)
