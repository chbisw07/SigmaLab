from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.orm import Instrument, Watchlist, WatchlistItem


@dataclass(frozen=True)
class WatchlistRepository:
    session: Session

    def create(self, name: str, description: str | None = None) -> Watchlist:
        wl = Watchlist(name=name, description=description)
        self.session.add(wl)
        self.session.commit()
        self.session.refresh(wl)
        return wl

    def get(self, watchlist_id: uuid.UUID) -> Watchlist | None:
        return self.session.get(Watchlist, watchlist_id)

    def list(self) -> list[Watchlist]:
        return list(self.session.execute(select(Watchlist).order_by(Watchlist.created_at.desc())).scalars())

    def rename(self, watchlist_id: uuid.UUID, name: str) -> Watchlist:
        wl = self.session.get(Watchlist, watchlist_id)
        if wl is None:
            raise KeyError("watchlist not found")
        wl.name = name
        self.session.commit()
        self.session.refresh(wl)
        return wl

    def delete(self, watchlist_id: uuid.UUID) -> None:
        wl = self.session.get(Watchlist, watchlist_id)
        if wl is None:
            return
        self.session.delete(wl)
        self.session.commit()

    def add_instrument(self, watchlist_id: uuid.UUID, instrument_id: uuid.UUID) -> None:
        item = WatchlistItem(watchlist_id=watchlist_id, instrument_id=instrument_id)
        self.session.add(item)
        try:
            self.session.commit()
        except IntegrityError:
            # Idempotent add: ignore duplicates (unique constraint enforced in PH2 migration).
            self.session.rollback()

    def remove_instrument(self, watchlist_id: uuid.UUID, instrument_id: uuid.UUID) -> None:
        stmt = select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.instrument_id == instrument_id,
        )
        item = self.session.execute(stmt).scalars().first()
        if item is None:
            return
        self.session.delete(item)
        self.session.commit()

    def list_instruments(self, watchlist_id: uuid.UUID) -> list[Instrument]:
        stmt = (
            select(Instrument)
            .join(WatchlistItem, WatchlistItem.instrument_id == Instrument.id)
            .where(WatchlistItem.watchlist_id == watchlist_id)
            .order_by(Instrument.symbol.asc())
        )
        return list(self.session.execute(stmt).scalars())

