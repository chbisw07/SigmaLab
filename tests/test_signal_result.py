from __future__ import annotations

from datetime import datetime

import pandas as pd

from strategies.context import IndicatorContext
from strategies.models import SignalResult


def test_indicator_context_caches_computations() -> None:
    ctx = IndicatorContext()
    calls = {"n": 0}

    def compute():  # type: ignore[no-untyped-def]
        calls["n"] += 1
        return pd.Series([1, 2, 3])

    a = ctx.get(("x", 1), compute)
    b = ctx.get(("x", 1), compute)
    assert calls["n"] == 1
    assert a.equals(b)


def test_signal_result_to_frame_is_deterministic() -> None:
    ts = pd.Series([datetime(2026, 3, 1), datetime(2026, 3, 2)])
    ind = pd.DataFrame({"ema": [1.0, 2.0]})
    out = SignalResult(
        timestamp=ts,
        indicators=ind,
        long_entry=pd.Series([True, False]),
        long_exit=pd.Series([False, True]),
        short_entry=pd.Series([False, False]),
        short_exit=pd.Series([False, False]),
        stop_loss=pd.Series([0.5, 1.5]),
        take_profit=None,
        metadata={"x": 1},
    )
    df = out.to_frame()
    assert list(df.columns) == [
        "timestamp",
        "long_entry",
        "long_exit",
        "short_entry",
        "short_exit",
        "stop_loss",
        "ema",
    ]
    assert df["long_entry"].dtype == bool

