from __future__ import annotations

import pytest

from app.optimization.search_space import SearchSpaceError, build_param_grid
from strategies.models import ParameterSpec


def test_build_param_grid_deterministic_keys_and_count() -> None:
    specs = [
        ParameterSpec(key="b", label="B", type="int", default=2, min=1, max=5, step=1, tunable=True),
        ParameterSpec(key="a", label="A", type="int", default=1, min=1, max=3, step=1, tunable=True),
    ]
    sel = {
        "b": {"mode": "range", "min": 1, "max": 3, "step": 1},
        "a": {"mode": "values", "values": [1, 2]},
    }
    grid = build_param_grid(specs=specs, selection=sel)
    assert grid.keys_sorted() == ["a", "b"]
    assert grid.combination_count() == 2 * 3
    combos = grid.enumerate()
    assert combos[0] == {"a": 1, "b": 1}
    assert combos[-1] == {"a": 2, "b": 3}


def test_build_param_grid_rejects_unknown_key() -> None:
    specs = [ParameterSpec(key="x", label="X", type="int", default=1, min=1, max=3, step=1, tunable=True)]
    with pytest.raises(SearchSpaceError, match="Unknown parameter keys"):
        build_param_grid(specs=specs, selection={"y": {"mode": "values", "values": [1]}})


def test_build_param_grid_rejects_non_tunable() -> None:
    specs = [ParameterSpec(key="x", label="X", type="int", default=1, min=1, max=3, step=1, tunable=False)]
    with pytest.raises(SearchSpaceError, match="not tunable"):
        build_param_grid(specs=specs, selection={"x": {"mode": "range", "min": 1, "max": 2, "step": 1}})


def test_build_param_grid_float_range_decimal_stability() -> None:
    specs = [ParameterSpec(key="f", label="F", type="float", default=0.0, min=0.0, max=1.0, step=0.1, tunable=True)]
    grid = build_param_grid(specs=specs, selection={"f": {"mode": "range", "min": 0.0, "max": 0.3, "step": 0.1}})
    vals = grid.values_by_key["f"]
    assert vals == [0.0, 0.1, 0.2, 0.3]


def test_build_param_grid_enum_and_bool_values() -> None:
    specs = [
        ParameterSpec(key="mode", label="Mode", type="enum", default="a", enum_values=("a", "b"), tunable=True),
        ParameterSpec(key="flag", label="Flag", type="bool", default=False, tunable=True),
    ]
    grid = build_param_grid(
        specs=specs,
        selection={
            "mode": {"mode": "values", "values": ["a", "b"]},
            "flag": {"mode": "values", "values": [True, False]},
        },
    )
    assert grid.combination_count() == 4

