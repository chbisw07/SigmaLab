from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from itertools import product
from typing import Any

from strategies.models import ParameterSpec


class SearchSpaceError(ValueError):
    pass


@dataclass(frozen=True)
class ParamGrid:
    """Validated, deterministic parameter grid definition."""

    values_by_key: dict[str, list[Any]]

    def keys_sorted(self) -> list[str]:
        return sorted(self.values_by_key.keys())

    def combination_count(self) -> int:
        n = 1
        for k in self.keys_sorted():
            n *= max(0, len(self.values_by_key[k]))
        return n

    def enumerate(self) -> list[dict[str, Any]]:
        keys = self.keys_sorted()
        if not keys:
            return [{}]
        vals = [self.values_by_key[k] for k in keys]
        out: list[dict[str, Any]] = []
        for combo in product(*vals):
            out.append({k: combo[i] for i, k in enumerate(keys)})
        return out


def build_param_grid(
    *,
    specs: list[ParameterSpec],
    selection: dict[str, dict[str, Any]],
    allow_nontunable: bool = False,
) -> ParamGrid:
    """Validate a user-provided selection into a deterministic grid.

    `selection` maps param_key -> config, where config is one of:
    - {"mode": "range", "min": x, "max": y, "step": s}
    - {"mode": "values", "values": [..]}
    """
    spec_by_key = {s.key: s for s in specs}

    unknown = sorted(set(selection.keys()) - set(spec_by_key.keys()))
    if unknown:
        raise SearchSpaceError(f"Unknown parameter keys: {unknown}")

    values_by_key: dict[str, list[Any]] = {}
    for key in sorted(selection.keys()):
        spec = spec_by_key[key]
        if not allow_nontunable and not spec.tunable:
            raise SearchSpaceError(f"Parameter '{key}' is not tunable")

        cfg = selection[key] or {}
        mode = cfg.get("mode")
        if mode not in {"range", "values"}:
            raise SearchSpaceError(f"Parameter '{key}': mode must be 'range' or 'values'")

        if mode == "values":
            values = cfg.get("values")
            if not isinstance(values, list) or not values:
                raise SearchSpaceError(f"Parameter '{key}': values must be a non-empty list")
            values_by_key[key] = _coerce_values(spec, values)
            continue

        # mode == "range"
        if spec.type not in {"int", "float"}:
            raise SearchSpaceError(f"Parameter '{key}': range mode is only supported for int/float params")
        try:
            vmin = cfg.get("min")
            vmax = cfg.get("max")
            step = cfg.get("step")
        except Exception as e:
            raise SearchSpaceError(f"Parameter '{key}': invalid range config") from e
        if vmin is None or vmax is None or step is None:
            raise SearchSpaceError(f"Parameter '{key}': min/max/step are required for range mode")

        values_by_key[key] = _range_values(spec, vmin, vmax, step)

    return ParamGrid(values_by_key=values_by_key)


def _coerce_values(spec: ParameterSpec, values: list[Any]) -> list[Any]:
    # Preserve input order but ensure deterministic JSON-friendly types.
    if spec.type == "bool":
        out: list[bool] = []
        for v in values:
            if isinstance(v, bool):
                out.append(v)
            elif isinstance(v, str) and v.lower() in {"true", "1", "yes", "y"}:
                out.append(True)
            elif isinstance(v, str) and v.lower() in {"false", "0", "no", "n"}:
                out.append(False)
            elif isinstance(v, (int, float)):
                out.append(bool(v))
            else:
                raise SearchSpaceError(f"{spec.key}: invalid bool value in values list")
        return out

    if spec.type == "enum":
        allowed = set(spec.enum_values or ())
        out: list[str] = []
        for v in values:
            sv = str(v)
            if sv not in allowed:
                raise SearchSpaceError(f"{spec.key}: value '{sv}' not in enum_values")
            out.append(sv)
        return out

    if spec.type == "int":
        out_i: list[int] = []
        for v in values:
            try:
                out_i.append(int(v))
            except Exception as e:
                raise SearchSpaceError(f"{spec.key}: invalid int value in values list") from e
        return out_i

    if spec.type == "float":
        out_f: list[float] = []
        for v in values:
            try:
                out_f.append(float(v))
            except Exception as e:
                raise SearchSpaceError(f"{spec.key}: invalid float value in values list") from e
        return out_f

    raise SearchSpaceError(f"{spec.key}: unsupported parameter type {spec.type}")


def _range_values(spec: ParameterSpec, vmin: Any, vmax: Any, step: Any) -> list[Any]:
    # Ensure range stays within spec bounds when provided.
    if spec.type == "int":
        try:
            a = int(vmin)
            b = int(vmax)
            s = int(step)
        except Exception as e:
            raise SearchSpaceError(f"{spec.key}: invalid int range values") from e
        if s <= 0:
            raise SearchSpaceError(f"{spec.key}: step must be > 0")
        if a > b:
            raise SearchSpaceError(f"{spec.key}: min must be <= max")
        if spec.min is not None and a < int(spec.min):
            raise SearchSpaceError(f"{spec.key}: min must be >= {spec.min}")
        if spec.max is not None and b > int(spec.max):
            raise SearchSpaceError(f"{spec.key}: max must be <= {spec.max}")
        return list(range(a, b + 1, s))

    # float: use Decimal to avoid drift; convert to float for persistence.
    try:
        a = Decimal(str(vmin))
        b = Decimal(str(vmax))
        s = Decimal(str(step))
    except (InvalidOperation, ValueError) as e:
        raise SearchSpaceError(f"{spec.key}: invalid float range values") from e
    if s <= 0:
        raise SearchSpaceError(f"{spec.key}: step must be > 0")
    if a > b:
        raise SearchSpaceError(f"{spec.key}: min must be <= max")
    if spec.min is not None and a < Decimal(str(spec.min)):
        raise SearchSpaceError(f"{spec.key}: min must be >= {spec.min}")
    if spec.max is not None and b > Decimal(str(spec.max)):
        raise SearchSpaceError(f"{spec.key}: max must be <= {spec.max}")

    vals: list[float] = []
    cur = a
    # Guard against runaway due to tiny steps.
    for _ in range(20000):
        if cur > b:
            break
        vals.append(float(cur))
        cur = cur + s
    if not vals:
        raise SearchSpaceError(f"{spec.key}: empty float range")
    return vals

