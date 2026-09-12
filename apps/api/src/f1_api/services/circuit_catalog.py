from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CircuitEngineeringData:
    track_length_km: float
    corners: int
    drs_zones: int
    clockwise: bool
    sector_count: int
    speed_trap_kmh: int


ENGINEERING_METADATA = {
    "Bahrain Grand Prix": CircuitEngineeringData(
        track_length_km=5.412,
        corners=15,
        drs_zones=3,
        clockwise=True,
        sector_count=3,
        speed_trap_kmh=322,
    ),
}