from __future__ import annotations

import pytest

from strategies.models import ParameterSpec
from strategies.params import ParameterValidationError, validate_params


def test_validate_params_applies_defaults_and_rejects_unknown_keys() -> None:
    specs = [
        ParameterSpec(key="n", label="N", type="int", default=10, min=1, max=20, step=1),
        ParameterSpec(key="flag", label="Flag", type="bool", default=False),
    ]
    out = validate_params(specs, raw={})
    assert out.values == {"n": 10, "flag": False}

    with pytest.raises(ParameterValidationError):
        validate_params(specs, raw={"unknown": 1})


def test_validate_params_coerces_types_and_enforces_ranges() -> None:
    specs = [
        ParameterSpec(key="n", label="N", type="int", default=10, min=1, max=20, step=1),
        ParameterSpec(key="x", label="X", type="float", default=1.5, min=0.0, max=10.0, step=0.5),
        ParameterSpec(key="b", label="B", type="bool", default=False),
        ParameterSpec(key="mode", label="Mode", type="enum", default="a", enum_values=("a", "b")),
    ]

    out = validate_params(specs, raw={"n": "2", "x": "2.5", "b": "true", "mode": "b"})
    assert out.values["n"] == 2
    assert out.values["x"] == 2.5
    assert out.values["b"] is True
    assert out.values["mode"] == "b"

    with pytest.raises(ParameterValidationError):
        validate_params(specs, raw={"n": 0})

    with pytest.raises(ParameterValidationError):
        validate_params(specs, raw={"mode": "nope"})

