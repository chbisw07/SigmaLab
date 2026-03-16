from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db_session
from app.models.schemas import ParameterPresetSchema
from app.services.repos.presets import ParameterPresetRepository
from app.services.repos.strategy_catalog import StrategyCatalogRepository
from strategies.models import ParameterSpec, StrategyMetadata
from strategies.params import ParameterValidationError
from strategies.service import StrategyService

router = APIRouter()


def _metadata_to_dict(m: StrategyMetadata) -> dict[str, Any]:
    return {
        "name": m.name,
        "slug": m.slug,
        "description": m.description,
        "category": m.category.value,
        "timeframe": m.timeframe,
        "long_only": m.long_only,
        "supported_segments": list(m.supported_segments),
        "version": m.version,
        "status": m.status.value,
        "notes": m.notes,
    }


def _param_to_dict(p: ParameterSpec) -> dict[str, Any]:
    return {
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


@router.get("")
def list_strategies() -> dict[str, Any]:
    svc = StrategyService.default()
    metas = svc.list_strategies()
    return {"status": "ok", "strategies": [_metadata_to_dict(m) for m in metas]}


@router.get("/{slug}")
def get_strategy(slug: str) -> dict[str, Any]:
    svc = StrategyService.default()
    try:
        detail = svc.get_detail(slug)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {
        "status": "ok",
        "metadata": _metadata_to_dict(detail.metadata),
        "parameters": [_param_to_dict(p) for p in detail.parameters],
    }


@router.post("/{slug}/validate")
def validate_strategy_params(slug: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    svc = StrategyService.default()
    try:
        validated = svc.validate(slug, params).values
        return {"status": "ok", "validated": validated}
    except (KeyError, ParameterValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{slug}/presets")
def list_presets(slug: str, session: Session = Depends(get_db_session)) -> dict[str, Any]:
    """List parameter presets for the current strategy version (PH5)."""
    svc = StrategyService.default()
    try:
        detail = svc.get_detail(slug)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    version = StrategyCatalogRepository(session).get_or_create_version(metadata=detail.metadata, parameters=detail.parameters)
    rows = ParameterPresetRepository(session).list_for_strategy_version(version.id, limit=200)
    return {"status": "ok", "presets": [ParameterPresetSchema.model_validate(p).model_dump() for p in rows]}


class PresetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    values: dict[str, Any]


@router.post("/{slug}/presets")
def create_preset(slug: str, payload: PresetCreate, session: Session = Depends(get_db_session)) -> dict[str, Any]:
    svc = StrategyService.default()
    try:
        detail = svc.get_detail(slug)
        validated = svc.validate(slug, payload.values).values
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ParameterValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    version = StrategyCatalogRepository(session).get_or_create_version(metadata=detail.metadata, parameters=detail.parameters)
    preset = ParameterPresetRepository(session).create(strategy_version_id=version.id, name=payload.name, values_json=validated)
    return {"status": "ok", "preset": ParameterPresetSchema.model_validate(preset).model_dump()}
