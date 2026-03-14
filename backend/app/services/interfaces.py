from __future__ import annotations

import uuid
from typing import Protocol


class BrokerConnectionService(Protocol):
    def get(self, connection_id: uuid.UUID) -> object: ...


class InstrumentService(Protocol):
    def get(self, instrument_id: uuid.UUID) -> object: ...


class WatchlistService(Protocol):
    def get(self, watchlist_id: uuid.UUID) -> object: ...


class StrategyRegistryService(Protocol):
    def get_strategy(self, strategy_id: uuid.UUID) -> object: ...


class BacktestRunService(Protocol):
    def get_run(self, run_id: uuid.UUID) -> object: ...


class OptimizationService(Protocol):
    def get_job(self, job_id: uuid.UUID) -> object: ...


class VisualizationReportService(Protocol):
    def get_report(self, report_id: uuid.UUID) -> object: ...

