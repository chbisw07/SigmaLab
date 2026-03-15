from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.backtesting.metrics import compute_drawdown
from app.backtesting.models import EquityPoint


def test_compute_drawdown_basic() -> None:
    t0 = datetime(2024, 1, 1, 9, 15, 0)
    curve = [
        EquityPoint(timestamp=t0, equity=1.0),
        EquityPoint(timestamp=t0 + timedelta(days=1), equity=0.9),
        EquityPoint(timestamp=t0 + timedelta(days=2), equity=1.1),
        EquityPoint(timestamp=t0 + timedelta(days=3), equity=1.05),
    ]
    dd = compute_drawdown(curve)
    # Max drawdown from 1.0 -> 0.9
    assert min(p.drawdown for p in dd) == pytest.approx(-0.1)
    # After new peak, drawdown resets.
    assert dd[2].drawdown == pytest.approx(0.0)
