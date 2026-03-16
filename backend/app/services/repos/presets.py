from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.orm import ParameterPreset


@dataclass(frozen=True)
class ParameterPresetRepository:
    session: Session

    def create(
        self,
        *,
        strategy_version_id: uuid.UUID,
        name: str,
        values_json: dict,
    ) -> ParameterPreset:
        row = ParameterPreset(
            strategy_version_id=strategy_version_id,
            name=name,
            values_json=values_json,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def list_for_strategy_version(self, strategy_version_id: uuid.UUID, limit: int = 200) -> list[ParameterPreset]:
        stmt = (
            select(ParameterPreset)
            .where(ParameterPreset.strategy_version_id == strategy_version_id)
            .order_by(ParameterPreset.created_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

