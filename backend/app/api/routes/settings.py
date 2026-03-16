from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_app_settings, get_db_session
from app.core.settings import Settings
from app.services.broker_settings import KiteBrokerSettingsService
from app.services.repos.broker_connections import BrokerConnectionRepository

router = APIRouter()


class KiteCredentialsUpsertRequest(BaseModel):
    """Upsert Zerodha/Kite credentials.

    Any field may be omitted or null to keep existing stored values unchanged.
    Empty strings are treated as null for convenience.
    """

    api_key: str | None = Field(default=None)
    api_secret: str | None = Field(default=None)
    access_token: str | None = Field(default=None)


def _none_if_blank(v: str | None) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return None if s == "" else s


def _svc(session: Session, settings: Settings) -> KiteBrokerSettingsService:
    repo = BrokerConnectionRepository(session)
    return KiteBrokerSettingsService(repo=repo, settings=settings)


@router.get("/broker/kite")
def get_kite_state(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    return _svc(session, settings).get_public_state()


@router.post("/broker/kite")
def save_kite_credentials(
    req: KiteCredentialsUpsertRequest,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    try:
        return _svc(session, settings).save_credentials(
            api_key=_none_if_blank(req.api_key),
            api_secret=_none_if_blank(req.api_secret),
            access_token=_none_if_blank(req.access_token),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/broker/kite/test")
def test_kite_connection(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    try:
        return _svc(session, settings).test_connection()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/broker/kite/clear-session")
def clear_kite_session(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    try:
        return _svc(session, settings).clear_session()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

