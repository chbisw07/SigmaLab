from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.orm import Instrument, Watchlist
from app.services.repos.watchlists import WatchlistRepository


@dataclass(frozen=True)
class WatchlistService:
    session: Session

    @property
    def repo(self) -> WatchlistRepository:
        return WatchlistRepository(self.session)

    def create(self, name: str, description: str | None = None) -> Watchlist:
        return self.repo.create(name=name, description=description)

    def list(self) -> list[Watchlist]:
        return self.repo.list()

    def rename(self, watchlist_id: uuid.UUID, name: str) -> Watchlist:
        return self.repo.rename(watchlist_id=watchlist_id, name=name)

    def delete(self, watchlist_id: uuid.UUID) -> None:
        self.repo.delete(watchlist_id)

    def add_instrument(self, watchlist_id: uuid.UUID, instrument_id: uuid.UUID) -> None:
        self.repo.add_instrument(watchlist_id, instrument_id)

    def remove_instrument(self, watchlist_id: uuid.UUID, instrument_id: uuid.UUID) -> None:
        self.repo.remove_instrument(watchlist_id, instrument_id)

    def list_instruments(self, watchlist_id: uuid.UUID) -> list[Instrument]:
        return self.repo.list_instruments(watchlist_id)

