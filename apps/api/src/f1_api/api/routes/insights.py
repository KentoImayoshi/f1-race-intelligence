from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from f1_api.api.schemas import TopDriverInsightRow
from f1_api.services.insights import load_top_driver_insights
from f1_core.config import settings

router = APIRouter(prefix=f"{settings.api_v1_prefix}")


@router.get("/insights/top-drivers", response_model=list[TopDriverInsightRow])
def get_top_driver_insights(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    limit: int = Query(20),
) -> list[TopDriverInsightRow]:
    try:
        return load_top_driver_insights(
            season=season, round_number=round_number, session=session, limit=limit
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
