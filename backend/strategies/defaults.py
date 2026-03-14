from __future__ import annotations

from functools import lru_cache

from strategies.builtin import IntradayVWAPPullbackStrategy, SwingTrendPullbackStrategy
from strategies.registry import StrategyRegistry


@lru_cache
def get_default_registry() -> StrategyRegistry:
    reg = StrategyRegistry()
    reg.register(SwingTrendPullbackStrategy)
    reg.register(IntradayVWAPPullbackStrategy)
    return reg

