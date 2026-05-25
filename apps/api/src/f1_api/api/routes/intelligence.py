from __future__ import annotations

from f1_core.config import settings
from fastapi import APIRouter, HTTPException, Query

from f1_api.api.schemas import (
    DriverIntelligenceReportRow,
    RaceTrendRow,
    SessionIntelligenceSummaryRow,
    StrategyInsightRow,
)
from f1_api.services.intelligence import (
    load_driver_intelligence_reports,
    load_race_trend_analysis,
    load_session_intelligence_summaries,
    load_strategy_insights,
)

router = APIRouter(prefix=f"{settings.api_v1_prefix}")


@router.get("/intelligence/session-summaries", response_model=list[SessionIntelligenceSummaryRow])
def get_session_intelligence_summaries(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    limit: int = Query(20),
) -> list[SessionIntelligenceSummaryRow]:
    try:
        return load_session_intelligence_summaries(
            season=season,
            round_number=round_number,
            session=session,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/intelligence/driver-reports", response_model=list[DriverIntelligenceReportRow])
def get_driver_intelligence_reports(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    driver_code: str | None = Query(None, alias="driver"),
    limit: int = Query(20),
) -> list[DriverIntelligenceReportRow]:
    try:
        return load_driver_intelligence_reports(
            season=season,
            round_number=round_number,
            session=session,
            driver_code=driver_code,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/intelligence/strategy-insights", response_model=list[StrategyInsightRow])
def get_strategy_insights(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    driver_code: str | None = Query(None, alias="driver"),
    limit: int = Query(20),
) -> list[StrategyInsightRow]:
    try:
        return load_strategy_insights(
            season=season,
            round_number=round_number,
            session=session,
            driver_code=driver_code,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/intelligence/race-trends", response_model=list[RaceTrendRow])
def get_race_trend_analysis(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    driver_code: str | None = Query(None, alias="driver"),
    limit: int = Query(50),
) -> list[RaceTrendRow]:
    try:
        return load_race_trend_analysis(
            season=season,
            round_number=round_number,
            session=session,
            driver_code=driver_code,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
