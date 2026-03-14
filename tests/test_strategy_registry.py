from __future__ import annotations

import pytest

from strategies.defaults import get_default_registry


def test_default_registry_contains_builtins() -> None:
    reg = get_default_registry()
    slugs = sorted([m.slug for m in reg.list_metadata()])
    assert slugs == ["intraday_vwap_pullback", "swing_trend_pullback"]


def test_registry_get_unknown_raises() -> None:
    reg = get_default_registry()
    with pytest.raises(KeyError):
        reg.get("does_not_exist")

