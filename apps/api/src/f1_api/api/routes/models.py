from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from f1_api.api.schemas import BaselineDriverScoreRow
from f1_api.services.models import load_baseline_driver_scores
from f1_core.config import settings

router = APIRouter(prefix=f"{settings.api_v1_prefix}")


@router.get("/models/baseline-driver-scores", response_model=list[BaselineDriverScoreRow])
def get_baseline_driver_scores(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    limit: int = Query(20),
    ) -> list[BaselineDriverScoreRow]:
    try:
        return load_baseline_driver_scores(
            season=season, round_number=round_number, session=session, limit=limit
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
