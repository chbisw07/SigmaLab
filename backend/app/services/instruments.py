from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol

from app.services.repos.instruments import InstrumentRepository


class KiteInstrumentsClient(Protocol):
    def instruments(self) -> list[dict]: ...


def _json_sanitize(value):  # type: ignore[no-untyped-def]
    """Convert common non-JSON types returned by broker SDKs into JSON values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_sanitize(v) for v in value]
    return str(value)


def normalize_kite_instrument(raw: dict) -> dict:
    """Normalize a Kite instrument row into SigmaLab's persisted shape."""
    token = raw.get("instrument_token")
    exchange = raw.get("exchange")
    symbol = raw.get("tradingsymbol") or raw.get("symbol")

    if token is None or exchange is None or symbol is None:
        raise ValueError("Kite instrument row missing required fields: instrument_token/exchange/tradingsymbol")

    return {
        "broker_instrument_token": str(token),
        "exchange": str(exchange),
        "symbol": str(symbol),
        "name": raw.get("name"),
        "segment": raw.get("segment"),
        "instrument_metadata": _json_sanitize(dict(raw)),
    }


@dataclass(frozen=True)
class InstrumentService:
    kite: KiteInstrumentsClient
    repo: InstrumentRepository

    def sync_instruments(self) -> int:
        rows = self.kite.instruments()
        normalized: list[dict] = []
        for r in rows:
            try:
                normalized.append(normalize_kite_instrument(r))
            except ValueError:
                # Skip rows that don't match the expected schema.
                continue
        return self.repo.upsert_many(normalized)
