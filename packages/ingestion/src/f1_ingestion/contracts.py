"""Contracts for raw ingestion outputs."""

from __future__ import annotations

from dataclasses import dataclass

RAW_SESSION_RESULTS_COLUMNS = [
    "season",
    "round",
    "session",
    "driver_code",
    "position",
    "lap_time_ms",
    "source",
    "ingested_at",
]

RAW_SESSION_LAPS_COLUMNS = [
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "lap_time_ms",
    "sector_1_ms",
    "sector_2_ms",
    "sector_3_ms",
    "compound",
    "stint",
    "is_personal_best",
    "source",
    "ingested_at",
]


@dataclass(frozen=True)
class RawSessionResult:
    season: int
    round: int
    session: str
    driver_code: str
    position: int
    lap_time_ms: int
    source: str
    ingested_at: str

    def to_record(self) -> dict[str, object]:
        return {
            "season": self.season,
            "round": self.round,
            "session": self.session,
            "driver_code": self.driver_code,
            "position": self.position,
            "lap_time_ms": self.lap_time_ms,
            "source": self.source,
            "ingested_at": self.ingested_at,
        }


@dataclass(frozen=True)
class RawSessionLap:
    season: int
    round: int
    grand_prix: str
    session: str
    driver_code: str
    lap_number: int
    lap_time_ms: int | None
    sector_1_ms: int | None
    sector_2_ms: int | None
    sector_3_ms: int | None
    compound: str | None
    stint: int | None
    is_personal_best: bool | None
    source: str
    ingested_at: str

    def to_record(self) -> dict[str, object]:
        return {
            "season": self.season,
            "round": self.round,
            "grand_prix": self.grand_prix,
            "session": self.session,
            "driver_code": self.driver_code,
            "lap_number": self.lap_number,
            "lap_time_ms": self.lap_time_ms,
            "sector_1_ms": self.sector_1_ms,
            "sector_2_ms": self.sector_2_ms,
            "sector_3_ms": self.sector_3_ms,
            "compound": self.compound,
            "stint": self.stint,
            "is_personal_best": self.is_personal_best,
            "source": self.source,
            "ingested_at": self.ingested_at,
        }
