from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from f1_api.services.pipeline import run_session_baseline_pipeline
from f1_core.config import settings

router = APIRouter(prefix=f"{settings.api_v1_prefix}")


class PipelineRequest(BaseModel):
    source: str = Field("seed", description="Data source, e.g. seed or fastf1")
    year: int | None = Field(None, description="Season year (required for fastf1)")
    round_value: str | None = Field(None, alias="round", description="Grand prix name or round")
    session: str | None = Field(None, description="Session code, e.g. R, Q, FP1")


@router.post("/pipeline/run-session-baseline")
def run_session_baseline(request: PipelineRequest) -> dict[str, Any]:
    try:
        return run_session_baseline_pipeline(
            source=request.source,
            year=request.year,
            round_value=request.round_value,
            session=request.session,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
