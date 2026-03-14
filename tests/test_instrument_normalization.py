from __future__ import annotations

from app.services.instruments import InstrumentService, normalize_kite_instrument


def test_normalize_kite_instrument_required_fields() -> None:
    raw = {
        "instrument_token": 123,
        "exchange": "NSE",
        "tradingsymbol": "RELIANCE",
        "name": "Reliance Industries",
        "segment": "NSE",
        "tick_size": 0.05,
    }
    out = normalize_kite_instrument(raw)
    assert out["broker_instrument_token"] == "123"
    assert out["exchange"] == "NSE"
    assert out["symbol"] == "RELIANCE"
    assert out["instrument_metadata"]["tick_size"] == 0.05


def test_instrument_service_sync_calls_repo_with_normalized_rows() -> None:
    class FakeKite:
        def instruments(self):  # type: ignore[no-untyped-def]
            return [
                {"instrument_token": 1, "exchange": "NSE", "tradingsymbol": "AAA"},
                {"instrument_token": 2, "exchange": "NSE", "tradingsymbol": "BBB"},
            ]

    class FakeRepo:
        def __init__(self):  # type: ignore[no-untyped-def]
            self.rows = None

        def upsert_many(self, instruments):  # type: ignore[no-untyped-def]
            self.rows = instruments
            return len(instruments)

    repo = FakeRepo()
    svc = InstrumentService(kite=FakeKite(), repo=repo)  # type: ignore[arg-type]
    n = svc.sync_instruments()

    assert n == 2
    assert repo.rows[0]["broker_instrument_token"] == "1"
    assert repo.rows[1]["symbol"] == "BBB"

