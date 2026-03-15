from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import Strategy, StrategyVersion
from strategies.models import ParameterSpec, StrategyMetadata


def _param_specs_to_schema(specs: list[ParameterSpec]) -> list[dict]:
    out: list[dict] = []
    for p in specs:
        out.append(
            {
                "key": p.key,
                "label": p.label,
                "type": p.type,
                "default": p.default,
                "description": p.description,
                "tunable": p.tunable,
                "min": p.min,
                "max": p.max,
                "step": p.step,
                "enum_values": list(p.enum_values) if p.enum_values else None,
                "grid_values": list(p.grid_values) if p.grid_values else None,
            }
        )
    return out


def _default_params(specs: list[ParameterSpec]) -> dict:
    return {p.key: p.default for p in specs}


@dataclass(frozen=True)
class StrategyCatalogRepository:
    """Persist code-registered strategies into the DB catalog.

    Backtest runs reference StrategyVersion IDs for reproducibility, even though strategies
    are implemented in code and discovered via the registry.
    """

    session: Session

    def get_or_create_version(
        self,
        *,
        metadata: StrategyMetadata,
        parameters: list[ParameterSpec],
    ) -> StrategyVersion:
        stmt = select(Strategy).where(Strategy.slug == metadata.slug)
        strategy = self.session.execute(stmt).scalars().first()
        if strategy is None:
            strategy = Strategy(
                name=metadata.name,
                slug=metadata.slug,
                category=metadata.category.value,
                description=metadata.description,
                code_ref=f"builtin:{metadata.slug}",
            )
            self.session.add(strategy)
            self.session.commit()
            self.session.refresh(strategy)
        else:
            # Keep DB strategy metadata reasonably up-to-date without requiring explicit migrations.
            strategy.name = metadata.name
            strategy.category = metadata.category.value
            strategy.description = metadata.description
            if strategy.code_ref is None:
                strategy.code_ref = f"builtin:{metadata.slug}"
            self.session.commit()

        v_stmt = (
            select(StrategyVersion)
            .where(StrategyVersion.strategy_id == strategy.id)
            .where(StrategyVersion.version == metadata.version)
        )
        version = self.session.execute(v_stmt).scalars().first()
        if version is None:
            version = StrategyVersion(
                strategy_id=strategy.id,
                version=metadata.version,
                changelog=None,
                parameter_schema=_param_specs_to_schema(parameters),
                default_params=_default_params(parameters),
            )
            self.session.add(version)
            self.session.commit()
            self.session.refresh(version)

        if strategy.current_version_id != version.id:
            strategy.current_version_id = version.id
            self.session.commit()

        return version

