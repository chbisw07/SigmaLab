"""SigmaLab Strategy Engine (PH3).

Strategies are declarative modules that:
- consume MarketDataService-compatible candles (no broker calls)
- produce signals + indicator outputs + parameter metadata

Important rule: strategies generate signals; simulation engines generate trades.
"""

