from __future__ import annotations

import enum
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal


class CloseReason(str, enum.Enum):
    STOP_LOSS = "stop_loss"
    TARGET_HIT = "target_hit"
    SIGNAL_EXIT = "signal_exit"
    TIME_EXIT = "time_exit"
    INTRADAY_SQUAREOFF = "intraday_squareoff"


EntryTiming = Literal["next_open"]
ExitTiming = Literal["next_open"]


@dataclass(frozen=True)
class ExecutionAssumptions:
    """Explicit, persisted assumptions for deterministic backtests (PH4).

    Defaults are intentionally conservative to avoid lookahead bias:
    - entries/exits execute on the next bar open after the signal bar closes
    - if stop-loss and take-profit are both hit in the same bar, stop-loss wins
    """

    entry_timing: EntryTiming = "next_open"
    exit_timing: ExitTiming = "next_open"
    stop_vs_target_precedence: Literal["stop_first", "target_first"] = "stop_first"
    long_only: bool = True
    one_position_at_a_time: bool = True

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Trade:
    run_id: uuid.UUID | None
    instrument_id: uuid.UUID | None
    symbol: str
    side: Literal["long", "short"]
    quantity: float
    entry_ts: datetime
    exit_ts: datetime
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    entry_reason: str | None
    close_reason: CloseReason
    exit_reason: str | None = None

    def to_orm_row(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "instrument_id": self.instrument_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "entry_ts": self.entry_ts,
            "exit_ts": self.exit_ts,
            "entry_price": float(self.entry_price),
            "exit_price": float(self.exit_price),
            "pnl": float(self.pnl),
            "pnl_pct": float(self.pnl_pct),
            "entry_reason": self.entry_reason,
            "exit_reason": self.exit_reason,
            "close_reason": self.close_reason.value,
        }


@dataclass(frozen=True)
class EquityPoint:
    timestamp: datetime
    equity: float

    def to_json(self) -> dict[str, Any]:
        # Use ISO string so FastAPI/JSON doesn't choke on datetime objects.
        return {"timestamp": self.timestamp.isoformat(), "equity": float(self.equity)}


@dataclass(frozen=True)
class DrawdownPoint:
    timestamp: datetime
    drawdown: float

    def to_json(self) -> dict[str, Any]:
        return {"timestamp": self.timestamp.isoformat(), "drawdown": float(self.drawdown)}


@dataclass(frozen=True)
class ReplayResult:
    trades: list[Trade]
    equity_curve: list[EquityPoint]

