from __future__ import annotations

from f1_core.config import settings
from fastapi import APIRouter, HTTPException, Query

from f1_api.api.schemas import (
    DriverConsistencyRow,
    PaceEvolutionRow,
    SessionLapAnalysisRow,
    TireStintSummaryRow,
)
from f1_api.services.analytics import (
    load_driver_consistency,
    load_driver_lap_comparison,
    load_pace_evolution,
    load_session_lap_analysis,
    load_tire_stint_summaries,
)

router = APIRouter(prefix=f"{settings.api_v1_prefix}")


@router.get("/analytics/session-lap-analysis", response_model=list[SessionLapAnalysisRow])
def get_session_lap_analysis(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    driver_code: str | None = Query(None, alias="driver"),
    limit: int = Query(200),
) -> list[SessionLapAnalysisRow]:
    try:
        return load_session_lap_analysis(
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


@router.get("/analytics/driver-lap-comparison", response_model=list[SessionLapAnalysisRow])
def get_driver_lap_comparison(
    driver: str = Query(...),
    compare_driver: str = Query(...),
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    limit: int = Query(200),
) -> list[SessionLapAnalysisRow]:
    try:
        return load_driver_lap_comparison(
            season=season,
            round_number=round_number,
            session=session,
            driver_code=driver,
            compare_driver=compare_driver,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/analytics/tire-stint-summaries", response_model=list[TireStintSummaryRow])
def get_tire_stint_summaries(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    driver_code: str | None = Query(None, alias="driver"),
    limit: int = Query(100),
) -> list[TireStintSummaryRow]:
    try:
        return load_tire_stint_summaries(
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


@router.get("/analytics/pace-evolution", response_model=list[PaceEvolutionRow])
def get_pace_evolution(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    driver_code: str | None = Query(None, alias="driver"),
    limit: int = Query(200),
) -> list[PaceEvolutionRow]:
    try:
        return load_pace_evolution(
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


@router.get("/analytics/driver-consistency", response_model=list[DriverConsistencyRow])
def get_driver_consistency(
    season: int | None = Query(None),
    round_number: int | None = Query(None, alias="round"),
    session: str | None = Query(None),
    limit: int = Query(50),
) -> list[DriverConsistencyRow]:
    try:
        return load_driver_consistency(
            season=season,
            round_number=round_number,
            session=session,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
