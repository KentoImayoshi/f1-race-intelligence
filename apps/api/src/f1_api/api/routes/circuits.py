from __future__ import annotations

from fastapi import APIRouter

from f1_core.config import settings
from f1_api.services.circuits import get_circuit_metadata
from f1_api.services.telemetry import get_track_coordinates

router = APIRouter(prefix=settings.api_v1_prefix)


@router.get("/circuits")
def circuit_metadata(year: int, round: int):
    return get_circuit_metadata(year, round)


@router.get("/circuits/track")
def circuit_track(year: int, round: int, session: str = "R"):
    return {
        "season": year,
        "round": round,
        "session": session,
        "track": get_track_coordinates(year, round, session),
    }