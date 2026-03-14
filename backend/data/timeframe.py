from __future__ import annotations

import enum
import re
from dataclasses import dataclass


class KiteInterval(str, enum.Enum):
    MINUTE = "minute"
    M3 = "3minute"
    M5 = "5minute"
    M10 = "10minute"
    M15 = "15minute"
    M30 = "30minute"
    H1 = "60minute"
    D1 = "day"


@dataclass(frozen=True)
class TimeframePlan:
    kite_interval: KiteInterval
    aggregation_factor: int
    calendar_rule: str | None = None

    @property
    def needs_aggregation(self) -> bool:
        return self.aggregation_factor > 1 or self.calendar_rule is not None


class Timeframe(str, enum.Enum):
    """User-visible timeframes.

    Kite only provides base intervals (minute, 3/5/10/15/30/60 minute, day). SigmaLab
    supports higher timeframes via aggregation.
    """

    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M10 = "10m"
    M15 = "15m"
    M30 = "30m"
    M45 = "45m"

    H1 = "1h"
    H2 = "2h"
    H4 = "4h"

    D1 = "1D"
    W1 = "1W"
    M1_MONTH = "1M"

    @classmethod
    def parse(cls, value: str) -> "Timeframe":
        v = value.strip()
        # Normalize common variants: 1H -> 1h, 1d -> 1D, etc.
        if re.fullmatch(r"\\d+[mMhHdDwW]", v):
            num = re.findall(r"\\d+", v)[0]
            unit = re.findall(r"[a-zA-Z]+", v)[0]
            if unit.lower() == "m":
                v = f"{num}m"
            elif unit.lower() == "h":
                v = f"{num}h"
            elif unit.lower() == "d":
                v = f"{num}D"
            elif unit.lower() == "w":
                v = f"{num}W"
        if v in ("1mo", "1MO", "1Month", "1MONTH"):
            v = "1M"
        try:
            return cls(v)
        except ValueError as e:
            raise ValueError(f"Unsupported timeframe: {value!r}") from e

    def base_interval(self) -> KiteInterval:
        return self.plan().kite_interval

    def aggregation_factor(self) -> int:
        return self.plan().aggregation_factor

    def plan(self) -> TimeframePlan:
        # Fixed-factor aggregations
        if self == Timeframe.M1:
            return TimeframePlan(KiteInterval.MINUTE, 1)
        if self == Timeframe.M3:
            return TimeframePlan(KiteInterval.M3, 1)
        if self == Timeframe.M5:
            return TimeframePlan(KiteInterval.M5, 1)
        if self == Timeframe.M10:
            return TimeframePlan(KiteInterval.M10, 1)
        if self == Timeframe.M15:
            return TimeframePlan(KiteInterval.M15, 1)
        if self == Timeframe.M30:
            return TimeframePlan(KiteInterval.M30, 1)
        if self == Timeframe.M45:
            return TimeframePlan(KiteInterval.M15, 3)

        if self == Timeframe.H1:
            return TimeframePlan(KiteInterval.H1, 1)
        if self == Timeframe.H2:
            return TimeframePlan(KiteInterval.H1, 2)
        if self == Timeframe.H4:
            return TimeframePlan(KiteInterval.H1, 4)

        if self == Timeframe.D1:
            return TimeframePlan(KiteInterval.D1, 1)

        # Calendar aggregations from daily bars. These are best-effort given
        # market holidays; callers should expect missing weeks/months.
        if self == Timeframe.W1:
            return TimeframePlan(KiteInterval.D1, 1, calendar_rule="W-FRI")
        if self == Timeframe.M1_MONTH:
            return TimeframePlan(KiteInterval.D1, 1, calendar_rule="M")

        raise ValueError(f"Unsupported timeframe: {self.value}")

