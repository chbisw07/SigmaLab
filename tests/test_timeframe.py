from __future__ import annotations

from data.timeframe import KiteInterval, Timeframe


def test_timeframe_parse_normalizes_case() -> None:
    assert Timeframe.parse("1H") == Timeframe.H1
    assert Timeframe.parse("1d") == Timeframe.D1
    assert Timeframe.parse("45m") == Timeframe.M45


def test_timeframe_plan_base_interval_and_factor() -> None:
    p = Timeframe.M45.plan()
    assert p.kite_interval == KiteInterval.M15
    assert p.aggregation_factor == 3
    assert p.calendar_rule is None

    p2 = Timeframe.H2.plan()
    assert p2.kite_interval == KiteInterval.H1
    assert p2.aggregation_factor == 2


def test_timeframe_calendar_resample_plan() -> None:
    p = Timeframe.W1.plan()
    assert p.kite_interval == KiteInterval.D1
    assert p.calendar_rule == "W-FRI"

