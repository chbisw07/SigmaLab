from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Type

from strategies.base import BaseStrategy, StrategyParams
from strategies.defaults import get_default_registry
from strategies.models import ParameterSpec, StrategyMetadata
from strategies.params import ParameterValidationError, validate_params
from strategies.registry import StrategyRegistry


@dataclass(frozen=True)
class StrategyDetail:
    metadata: StrategyMetadata
    parameters: list[ParameterSpec]


@dataclass(frozen=True)
class StrategyService:
    registry: StrategyRegistry

    @classmethod
    def default(cls) -> "StrategyService":
        return cls(registry=get_default_registry())

    def list_strategies(self) -> list[StrategyMetadata]:
        metas = self.registry.list_metadata()
        return sorted(metas, key=lambda m: m.slug)

    def get_detail(self, slug: str) -> StrategyDetail:
        cls_ = self.registry.get(slug)
        return StrategyDetail(metadata=cls_.metadata(), parameters=cls_.parameters())

    def validate(self, slug: str, raw_params: dict[str, Any] | None) -> StrategyParams:
        cls_ = self.registry.get(slug)
        specs = cls_.parameters()
        validated = validate_params(specs, raw_params)
        return StrategyParams(values=validated.values)

    def instantiate(self, slug: str) -> BaseStrategy:
        cls_ = self.registry.get(slug)
        # Keep strategies stateless for PH3. Params are passed into generate_signals.
        return cls_()


def validate_params_for_api(service: StrategyService, slug: str, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Helper for API responses: return either validated values or a structured error."""
    try:
        params = service.validate(slug, raw)
        return {"status": "ok", "validated": params.values}
    except (KeyError, ParameterValidationError) as e:
        return {"status": "error", "error": str(e)}
