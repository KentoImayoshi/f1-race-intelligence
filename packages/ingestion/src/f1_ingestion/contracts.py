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
