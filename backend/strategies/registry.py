from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from strategies.base import BaseStrategy
from strategies.models import StrategyMetadata


@dataclass
class StrategyRegistry:
    _by_slug: dict[str, Type[BaseStrategy]]

    def __init__(self) -> None:
        self._by_slug = {}

    def register(self, strategy_cls: Type[BaseStrategy]) -> None:
        meta = strategy_cls.metadata()
        slug = meta.slug.strip()
        if not slug:
            raise ValueError("strategy slug must be non-empty")
        if slug in self._by_slug:
            raise ValueError(f"strategy already registered: {slug}")
        self._by_slug[slug] = strategy_cls

    def list_metadata(self) -> list[StrategyMetadata]:
        return [cls.metadata() for cls in self._by_slug.values()]

    def get(self, slug: str) -> Type[BaseStrategy]:
        try:
            return self._by_slug[slug]
        except KeyError as e:
            raise KeyError(f"unknown strategy: {slug}") from e

    def has(self, slug: str) -> bool:
        return slug in self._by_slug

