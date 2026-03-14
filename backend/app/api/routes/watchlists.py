from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db_session
from app.models.schemas import InstrumentSchema, WatchlistSchema
from app.services.watchlists import WatchlistService

router = APIRouter()


class WatchlistCreate(BaseModel):
    name: str
    description: str | None = None


class WatchlistRename(BaseModel):
    name: str


@router.post("", response_model=WatchlistSchema)
def create_watchlist(payload: WatchlistCreate, session: Session = Depends(get_db_session)):
    svc = WatchlistService(session)
    try:
        return svc.create(name=payload.name, description=payload.description)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=list[WatchlistSchema])
def list_watchlists(session: Session = Depends(get_db_session)):
    return WatchlistService(session).list()


@router.patch("/{watchlist_id}", response_model=WatchlistSchema)
def rename_watchlist(watchlist_id: uuid.UUID, payload: WatchlistRename, session: Session = Depends(get_db_session)):
    svc = WatchlistService(session)
    try:
        return svc.rename(watchlist_id=watchlist_id, name=payload.name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/{watchlist_id}")
def delete_watchlist(watchlist_id: uuid.UUID, session: Session = Depends(get_db_session)):
    WatchlistService(session).delete(watchlist_id=watchlist_id)
    return {"status": "ok"}


@router.post("/{watchlist_id}/items/{instrument_id}")
def add_watchlist_instrument(
    watchlist_id: uuid.UUID, instrument_id: uuid.UUID, session: Session = Depends(get_db_session)
):
    WatchlistService(session).add_instrument(watchlist_id=watchlist_id, instrument_id=instrument_id)
    return {"status": "ok"}


@router.delete("/{watchlist_id}/items/{instrument_id}")
def remove_watchlist_instrument(
    watchlist_id: uuid.UUID, instrument_id: uuid.UUID, session: Session = Depends(get_db_session)
):
    WatchlistService(session).remove_instrument(watchlist_id=watchlist_id, instrument_id=instrument_id)
    return {"status": "ok"}


@router.get("/{watchlist_id}/items", response_model=list[InstrumentSchema])
def list_watchlist_instruments(watchlist_id: uuid.UUID, session: Session = Depends(get_db_session)):
    return WatchlistService(session).list_instruments(watchlist_id=watchlist_id)

