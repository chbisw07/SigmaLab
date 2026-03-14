from __future__ import annotations

from typing import Protocol


class ResearchEngine(Protocol):
    """Fast, watchlist-wide research engine (vectorized in later phases)."""

    def run(self, *args, **kwargs) -> object: ...


class SimulationEngine(Protocol):
    """Event-driven engine that turns signals into trades.

    Important rule (PRD): strategy modules generate signals and metadata; simulation
    engines generate trades.
    """

    def run(self, *args, **kwargs) -> object: ...

