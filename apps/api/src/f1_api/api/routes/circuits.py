from __future__ import annotations

from fastapi import APIRouter, HTTPException

from f1_api.services.circuits import get_circuit_metadata
from f1_core.config import settings

router = APIRouter(prefix=settings.api_v1_prefix, tags=["circuits"])


@router.get("/circuits")
def circuit_metadata(year: int, round: int):
    try:
        return get_circuit_metadata(year, round)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc