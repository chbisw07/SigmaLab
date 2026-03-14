from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from strategies.models import ParameterSpec


class ParameterValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidatedParams:
    values: dict[str, Any]


def validate_params(specs: list[ParameterSpec], raw: dict[str, Any] | None) -> ValidatedParams:
    raw = raw or {}
    allowed = {s.key for s in specs}
    extra = sorted(set(raw.keys()) - allowed)
    if extra:
        raise ParameterValidationError(f"Unknown parameter keys: {extra}")

    out: dict[str, Any] = {}
    for spec in specs:
        val = raw.get(spec.key, spec.default)
        out[spec.key] = _coerce_and_validate(spec, val)
    return ValidatedParams(values=out)


def _coerce_and_validate(spec: ParameterSpec, value: Any) -> Any:
    t = spec.type

    if t == "bool":
        if isinstance(value, bool):
            v = value
        elif isinstance(value, str):
            if value.lower() in {"true", "1", "yes", "y"}:
                v = True
            elif value.lower() in {"false", "0", "no", "n"}:
                v = False
            else:
                raise ParameterValidationError(f"{spec.key}: invalid bool value")
        elif isinstance(value, (int, float)):
            v = bool(value)
        else:
            raise ParameterValidationError(f"{spec.key}: invalid bool value")
        return v

    if t == "int":
        try:
            v = int(value)
        except Exception as e:
            raise ParameterValidationError(f"{spec.key}: invalid int value") from e
        _validate_range(spec, v)
        _validate_step(spec, v)
        return v

    if t == "float":
        try:
            v = float(value)
        except Exception as e:
            raise ParameterValidationError(f"{spec.key}: invalid float value") from e
        _validate_range(spec, v)
        _validate_step(spec, v)
        return v

    if t == "enum":
        if spec.enum_values is None or not spec.enum_values:
            raise ParameterValidationError(f"{spec.key}: enum_values must be defined")
        v = str(value)
        if v not in spec.enum_values:
            raise ParameterValidationError(f"{spec.key}: must be one of {list(spec.enum_values)}")
        return v

    raise ParameterValidationError(f"{spec.key}: unsupported param type {t}")


def _validate_range(spec: ParameterSpec, v: int | float) -> None:
    if spec.min is not None and v < spec.min:
        raise ParameterValidationError(f"{spec.key}: must be >= {spec.min}")
    if spec.max is not None and v > spec.max:
        raise ParameterValidationError(f"{spec.key}: must be <= {spec.max}")


def _validate_step(spec: ParameterSpec, v: int | float) -> None:
    if spec.step is None:
        return
    # Step is advisory for UI/optimization; enforce only for ints to avoid float fuzz.
    if spec.type == "int":
        if spec.min is not None and ((v - int(spec.min)) % int(spec.step) != 0):
            raise ParameterValidationError(f"{spec.key}: must align to step {spec.step}")

