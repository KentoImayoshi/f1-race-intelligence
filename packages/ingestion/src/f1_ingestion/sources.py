"""Source adapters for real F1 session ingestion."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from math import isfinite
from typing import Mapping, Sequence

import httpx

from f1_ingestion.contracts import RawSessionLap, RawSessionResult, RawSessionTelemetry

FASTF1_SOURCE = "fastf1"
JOLPICA_SOURCE = "jolpica"
OPENF1_SOURCE = "openf1"
SEED_SOURCE = "seed"

OPENF1_BASE_URL = "https://api.openf1.org/v1"
JOLPICA_BASE_URL = "https://api.jolpi.ca/ergast/f1"
DEFAULT_HTTP_TIMEOUT_SECONDS = 30.0
DEFAULT_USER_AGENT = "f1-race-intelligence-ai/0.1"

SESSION_CODE_TO_OPENF1_NAME = {
    "FP1": "Practice 1",
    "FP2": "Practice 2",
    "FP3": "Practice 3",
    "Q": "Qualifying",
    "SQ": "Sprint Qualifying",
    "S": "Sprint",
    "R": "Race",
}

SESSION_CODE_TO_JOLPICA_DATASET = {
    "Q": "qualifying",
    "R": "results",
    "S": "sprint",
}


@dataclass(frozen=True)
class SourceRequest:
    source: str
    year: int | None
    grand_prix: str | int | None
    session: str | None


@dataclass(frozen=True)
class SourceMetadata:
    source: str
    fetched_at: str
    requested_year: int | None
    requested_grand_prix: str | None
    requested_session: str | None
    resolved_year: int | None = None
    resolved_round: int | None = None
    resolved_grand_prix: str | None = None
    resolved_session: str | None = None
    upstream_endpoints: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    result_row_count: int = 0
    lap_row_count: int = 0
    telemetry_row_count: int = 0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class SessionPayload:
    results: list[RawSessionResult]
    metadata: SourceMetadata


@dataclass(frozen=True)
class LapPayload:
    laps: list[RawSessionLap]
    metadata: SourceMetadata


@dataclass(frozen=True)
class TelemetryPayload:
    telemetry: list[RawSessionTelemetry]
    metadata: SourceMetadata


@dataclass(frozen=True)
class ResolvedOpenF1Session:
    year: int
    round_number: int
    grand_prix: str
    session_code: str
    session_key: int
    meeting_key: int


@dataclass(frozen=True)
class ResolvedJolpicaRound:
    year: int
    round_number: int
    grand_prix: str


def load_session_payload(request: SourceRequest, *, fetched_at: str) -> SessionPayload:
    if request.source == SEED_SOURCE:
        results = _seed_session_results(fetched_at)
        metadata = SourceMetadata(
            source=SEED_SOURCE,
            fetched_at=fetched_at,
            requested_year=request.year,
            requested_grand_prix=_stringify(request.grand_prix),
            requested_session=request.session,
            resolved_year=2024,
            resolved_round=1,
            resolved_grand_prix="Bahrain Grand Prix",
            resolved_session="R",
            upstream_endpoints=[],
            warnings=[],
            result_row_count=len(results),
            lap_row_count=0,
        )
        return SessionPayload(results=results, metadata=metadata)

    if request.source == FASTF1_SOURCE:
        return _fastf1_results_payload(request=request, fetched_at=fetched_at)
    if request.source == OPENF1_SOURCE:
        return _openf1_results_payload(request=request, fetched_at=fetched_at)
    if request.source == JOLPICA_SOURCE:
        return _jolpica_results_payload(request=request, fetched_at=fetched_at)

    raise ValueError(f"Unknown ingestion source: {request.source}")


def load_lap_payload(request: SourceRequest, *, fetched_at: str) -> LapPayload:
    if request.source == SEED_SOURCE:
        laps = _seed_session_laps(fetched_at)
        metadata = SourceMetadata(
            source=SEED_SOURCE,
            fetched_at=fetched_at,
            requested_year=request.year,
            requested_grand_prix=_stringify(request.grand_prix),
            requested_session=request.session,
            resolved_year=2024,
            resolved_round=1,
            resolved_grand_prix="Bahrain Grand Prix",
            resolved_session="R",
            upstream_endpoints=[],
            warnings=[],
            result_row_count=0,
            lap_row_count=len(laps),
            telemetry_row_count=0,
        )
        return LapPayload(laps=laps, metadata=metadata)
    if request.source == FASTF1_SOURCE:
        return _fastf1_laps_payload(request=request, fetched_at=fetched_at)
    if request.source == OPENF1_SOURCE:
        return _openf1_laps_payload(request=request, fetched_at=fetched_at)
    if request.source == JOLPICA_SOURCE:
        return _jolpica_laps_payload(request=request, fetched_at=fetched_at)
    raise ValueError(
        "Lap-level raw ingestion currently supports only the fastf1, openf1, and jolpica sources"
    )


def load_telemetry_payload(request: SourceRequest, *, fetched_at: str) -> TelemetryPayload:
    if request.source == SEED_SOURCE:
        telemetry = _seed_session_telemetry(fetched_at)
        metadata = SourceMetadata(
            source=SEED_SOURCE,
            fetched_at=fetched_at,
            requested_year=request.year,
            requested_grand_prix=_stringify(request.grand_prix),
            requested_session=request.session,
            resolved_year=2024,
            resolved_round=1,
            resolved_grand_prix="Bahrain Grand Prix",
            resolved_session="R",
            upstream_endpoints=[],
            warnings=[],
            result_row_count=0,
            lap_row_count=0,
            telemetry_row_count=len(telemetry),
        )
        return TelemetryPayload(telemetry=telemetry, metadata=metadata)
    if request.source == FASTF1_SOURCE:
        return _fastf1_telemetry_payload(request=request, fetched_at=fetched_at)
    if request.source == OPENF1_SOURCE:
        return _openf1_telemetry_payload(request=request, fetched_at=fetched_at)
    if request.source == JOLPICA_SOURCE:
        return _jolpica_telemetry_payload(request=request, fetched_at=fetched_at)
    raise ValueError(
        "Telemetry ingestion currently supports only the seed, fastf1, openf1, and jolpica sources"
    )


def _seed_session_results(ingested_at: str) -> list[RawSessionResult]:
    return [
        RawSessionResult(
            season=2024,
            round=1,
            session="R",
            driver_code="VER",
            position=1,
            lap_time_ms=5361234,
            source=SEED_SOURCE,
            ingested_at=ingested_at,
        ),
        RawSessionResult(
            season=2024,
            round=1,
            session="R",
            driver_code="PER",
            position=2,
            lap_time_ms=5369876,
            source=SEED_SOURCE,
            ingested_at=ingested_at,
        ),
        RawSessionResult(
            season=2024,
            round=1,
            session="R",
            driver_code="LEC",
            position=3,
            lap_time_ms=5374321,
            source=SEED_SOURCE,
            ingested_at=ingested_at,
        ),
    ]


def _seed_session_laps(ingested_at: str) -> list[RawSessionLap]:
    seed_rows = [
        ("VER", 1, 92450, 30400, 30950, 31100, "SOFT", 1, False),
        ("VER", 2, 91880, 30120, 30780, 30980, "SOFT", 1, True),
        ("VER", 3, 92210, 30310, 30840, 31060, "SOFT", 1, False),
        ("PER", 1, 92980, 30620, 31140, 31220, "SOFT", 1, False),
        ("PER", 2, 92540, 30480, 30970, 31090, "SOFT", 1, True),
        ("PER", 3, 92810, 30570, 31020, 31220, "SOFT", 1, False),
        ("LEC", 1, 93210, 30740, 31190, 31280, "MEDIUM", 1, False),
        ("LEC", 2, 92890, 30560, 31040, 31290, "MEDIUM", 1, True),
        ("LEC", 3, 93040, 30600, 31110, 31330, "MEDIUM", 1, False),
    ]
    return [
        RawSessionLap(
            season=2024,
            round=1,
            grand_prix="Bahrain Grand Prix",
            session="R",
            driver_code=driver_code,
            lap_number=lap_number,
            lap_time_ms=lap_time_ms,
            sector_1_ms=sector_1_ms,
            sector_2_ms=sector_2_ms,
            sector_3_ms=sector_3_ms,
            compound=compound,
            stint=stint,
            is_personal_best=is_personal_best,
            source=SEED_SOURCE,
            ingested_at=ingested_at,
        )
        for (
            driver_code,
            lap_number,
            lap_time_ms,
            sector_1_ms,
            sector_2_ms,
            sector_3_ms,
            compound,
            stint,
            is_personal_best,
        ) in seed_rows
    ]


def _seed_session_telemetry(ingested_at: str) -> list[RawSessionTelemetry]:
    seed_rows = [
        ("VER", 1, 205, 244, 288, 321, 3, "1", False, False),
        ("VER", 2, 207, 246, 290, 324, 4, "1", False, False),
        ("VER", 3, 206, 245, 289, 322, 5, "1", False, False),
        ("PER", 1, 201, 240, 284, 318, 3, "1", False, False),
        ("PER", 2, 203, 242, 286, 320, 4, "1", False, False),
        ("PER", 3, 202, 241, 285, 319, 5, "1", False, False),
        ("LEC", 1, 199, 238, 283, 316, 3, "1", False, False),
        ("LEC", 2, 200, 239, 284, 317, 4, "1", False, False),
        ("LEC", 3, 200, 239, 283, 316, 5, "1", False, False),
    ]
    return [
        RawSessionTelemetry(
            season=2024,
            round=1,
            grand_prix="Bahrain Grand Prix",
            session="R",
            driver_code=driver_code,
            lap_number=lap_number,
            speed_i1_kph=speed_i1_kph,
            speed_i2_kph=speed_i2_kph,
            speed_fl_kph=speed_fl_kph,
            speed_st_kph=speed_st_kph,
            tyre_life_laps=tyre_life_laps,
            track_status=track_status,
            is_pit_out_lap=is_pit_out_lap,
            is_pit_in_lap=is_pit_in_lap,
            source=SEED_SOURCE,
            ingested_at=ingested_at,
        )
        for (
            driver_code,
            lap_number,
            speed_i1_kph,
            speed_i2_kph,
            speed_fl_kph,
            speed_st_kph,
            tyre_life_laps,
            track_status,
            is_pit_out_lap,
            is_pit_in_lap,
        ) in seed_rows
    ]


def _fastf1_results_payload(*, request: SourceRequest, fetched_at: str) -> SessionPayload:
    if request.year is None or request.grand_prix is None or request.session is None:
        raise ValueError("year, grand_prix, and session are required for fastf1 ingestion")
    year, grand_prix, session = request.year, request.grand_prix, request.session
    session_obj = _load_fastf1_session(year=year, grand_prix=grand_prix, session=session)
    results = getattr(session_obj, "results", None)
    if results is None:
        raise RuntimeError("FastF1 session results are unavailable for this session.")

    round_number = int(session_obj.event["RoundNumber"])
    mapped = map_fastf1_results(
        season=year,
        round_number=round_number,
        session=session,
        results=_records_from_frame_like(results),
        ingested_at=fetched_at,
    )

    metadata = SourceMetadata(
        source=FASTF1_SOURCE,
        fetched_at=fetched_at,
        requested_year=request.year,
        requested_grand_prix=_stringify(request.grand_prix),
        requested_session=request.session,
        resolved_year=year,
        resolved_round=round_number,
        resolved_grand_prix=_resolve_event_name(getattr(session_obj, "event", None), grand_prix),
        resolved_session=session,
        upstream_endpoints=["fastf1.get_session"],
        warnings=[],
        result_row_count=len(mapped),
        lap_row_count=0,
    )
    return SessionPayload(results=mapped, metadata=metadata)


def _fastf1_laps_payload(*, request: SourceRequest, fetched_at: str) -> LapPayload:
    if request.year is None or request.grand_prix is None or request.session is None:
        raise ValueError("year, grand_prix, and session are required for fastf1 ingestion")
    year, grand_prix, session = request.year, request.grand_prix, request.session
    session_obj = _load_fastf1_session(year=year, grand_prix=grand_prix, session=session)
    laps = getattr(session_obj, "laps", None)
    if laps is None:
        raise RuntimeError("FastF1 session laps are unavailable for this session.")

    round_number = int(session_obj.event["RoundNumber"])
    event_name = _resolve_event_name(getattr(session_obj, "event", None), grand_prix)
    mapped = map_fastf1_laps(
        season=year,
        round_number=round_number,
        grand_prix=event_name,
        session=session,
        laps=_records_from_frame_like(laps),
        ingested_at=fetched_at,
    )

    metadata = SourceMetadata(
        source=FASTF1_SOURCE,
        fetched_at=fetched_at,
        requested_year=request.year,
        requested_grand_prix=_stringify(request.grand_prix),
        requested_session=request.session,
        resolved_year=year,
        resolved_round=round_number,
        resolved_grand_prix=event_name,
        resolved_session=session,
        upstream_endpoints=["fastf1.get_session"],
        warnings=[],
        result_row_count=0,
        lap_row_count=len(mapped),
    )
    return LapPayload(laps=mapped, metadata=metadata)


def _fastf1_telemetry_payload(*, request: SourceRequest, fetched_at: str) -> TelemetryPayload:
    if request.year is None or request.grand_prix is None or request.session is None:
        raise ValueError("year, grand_prix, and session are required for fastf1 ingestion")
    year, grand_prix, session = request.year, request.grand_prix, request.session
    session_obj = _load_fastf1_session(year=year, grand_prix=grand_prix, session=session)
    laps = getattr(session_obj, "laps", None)
    if laps is None:
        raise RuntimeError("FastF1 telemetry detail is unavailable for this session.")

    round_number = int(session_obj.event["RoundNumber"])
    event_name = _resolve_event_name(getattr(session_obj, "event", None), grand_prix)
    records = _records_from_frame_like(laps)
    telemetry = map_fastf1_telemetry(
        season=year,
        round_number=round_number,
        grand_prix=event_name,
        session=session,
        laps=records,
        ingested_at=fetched_at,
    )

    metadata = SourceMetadata(
        source=FASTF1_SOURCE,
        fetched_at=fetched_at,
        requested_year=request.year,
        requested_grand_prix=_stringify(request.grand_prix),
        requested_session=request.session,
        resolved_year=year,
        resolved_round=round_number,
        resolved_grand_prix=event_name,
        resolved_session=session,
        upstream_endpoints=["fastf1.get_session"],
        warnings=[],
        result_row_count=0,
        lap_row_count=0,
        telemetry_row_count=len(telemetry),
    )
    return TelemetryPayload(telemetry=telemetry, metadata=metadata)


def _openf1_results_payload(*, request: SourceRequest, fetched_at: str) -> SessionPayload:
    year, grand_prix, session = _require_context(request)
    resolved = _resolve_openf1_session(year=year, grand_prix=grand_prix, session=session)
    driver_map, driver_endpoint = _openf1_driver_map(resolved.session_key)
    result_endpoint = f"{OPENF1_BASE_URL}/session_result"
    lap_endpoint = f"{OPENF1_BASE_URL}/laps"

    result_rows = _get_json(
        result_endpoint,
        params={"session_key": resolved.session_key},
        source=OPENF1_SOURCE,
    )
    lap_rows = _get_json(
        lap_endpoint,
        params={"session_key": resolved.session_key},
        source=OPENF1_SOURCE,
    )

    best_laps = _openf1_best_lap_times(lap_rows)
    warnings: list[str] = []
    records: list[RawSessionResult] = []
    for index, row in enumerate(_expect_list(result_rows, source=OPENF1_SOURCE)):
        driver_number = _optional_int(row.get("driver_number"))
        driver_code = _driver_code_from_openf1_row(row, driver_map.get(driver_number))
        position = _coalesce_position(
            row.get("position"),
            fallback_index=index,
            warnings=warnings,
            provider=OPENF1_SOURCE,
            driver_code=driver_code,
        )
        lap_time_ms = _parse_optional_time_to_ms(
            row.get("fastest_lap_time") or row.get("best_lap_time")
        )
        if lap_time_ms is None and driver_number is not None:
            lap_time_ms = best_laps.get(driver_number)
        records.append(
            RawSessionResult(
                season=resolved.year,
                round=resolved.round_number,
                session=resolved.session_code,
                driver_code=driver_code,
                position=position,
                lap_time_ms=lap_time_ms or 0,
                source=OPENF1_SOURCE,
                ingested_at=fetched_at,
            )
        )

    if not records:
        raise RuntimeError("OpenF1 session results returned no rows for this session.")

    metadata = SourceMetadata(
        source=OPENF1_SOURCE,
        fetched_at=fetched_at,
        requested_year=request.year,
        requested_grand_prix=_stringify(request.grand_prix),
        requested_session=request.session,
        resolved_year=resolved.year,
        resolved_round=resolved.round_number,
        resolved_grand_prix=resolved.grand_prix,
        resolved_session=resolved.session_code,
        upstream_endpoints=[
            _render_endpoint(result_endpoint, {"session_key": resolved.session_key}),
            driver_endpoint,
            _render_endpoint(lap_endpoint, {"session_key": resolved.session_key}),
        ],
        warnings=warnings,
        result_row_count=len(records),
        lap_row_count=0,
    )
    return SessionPayload(results=records, metadata=metadata)


def _openf1_laps_payload(*, request: SourceRequest, fetched_at: str) -> LapPayload:
    year, grand_prix, session = _require_context(request)
    resolved = _resolve_openf1_session(year=year, grand_prix=grand_prix, session=session)
    driver_map, driver_endpoint = _openf1_driver_map(resolved.session_key)
    lap_endpoint = f"{OPENF1_BASE_URL}/laps"
    rows = _expect_list(
        _get_json(lap_endpoint, params={"session_key": resolved.session_key}, source=OPENF1_SOURCE),
        source=OPENF1_SOURCE,
    )

    warnings: list[str] = []
    records: list[RawSessionLap] = []
    for row in rows:
        driver_number = _optional_int(row.get("driver_number"))
        driver_code = _driver_code_from_openf1_row(row, driver_map.get(driver_number))
        lap_number = _optional_int(row.get("lap_number"))
        if lap_number is None:
            warnings.append(f"Skipped OpenF1 lap row for {driver_code}: missing lap_number.")
            continue
        records.append(
            RawSessionLap(
                season=resolved.year,
                round=resolved.round_number,
                grand_prix=resolved.grand_prix,
                session=resolved.session_code,
                driver_code=driver_code,
                lap_number=lap_number,
                lap_time_ms=_parse_optional_time_to_ms(row.get("lap_duration")),
                sector_1_ms=_parse_optional_time_to_ms(row.get("duration_sector_1")),
                sector_2_ms=_parse_optional_time_to_ms(row.get("duration_sector_2")),
                sector_3_ms=_parse_optional_time_to_ms(row.get("duration_sector_3")),
                compound=_optional_string(row.get("compound")),
                stint=_optional_int(row.get("stint_number")),
                is_personal_best=None,
                source=OPENF1_SOURCE,
                ingested_at=fetched_at,
            )
        )

    if not records:
        raise RuntimeError("OpenF1 session laps returned no usable rows for this session.")

    metadata = SourceMetadata(
        source=OPENF1_SOURCE,
        fetched_at=fetched_at,
        requested_year=request.year,
        requested_grand_prix=_stringify(request.grand_prix),
        requested_session=request.session,
        resolved_year=resolved.year,
        resolved_round=resolved.round_number,
        resolved_grand_prix=resolved.grand_prix,
        resolved_session=resolved.session_code,
        upstream_endpoints=[
            driver_endpoint,
            _render_endpoint(lap_endpoint, {"session_key": resolved.session_key}),
        ],
        warnings=warnings,
        result_row_count=0,
        lap_row_count=len(records),
    )
    return LapPayload(laps=records, metadata=metadata)


def _openf1_telemetry_payload(*, request: SourceRequest, fetched_at: str) -> TelemetryPayload:
    year, grand_prix, session = _require_context(request)
    resolved = _resolve_openf1_session(year=year, grand_prix=grand_prix, session=session)
    driver_map, driver_endpoint = _openf1_driver_map(resolved.session_key)
    lap_endpoint = f"{OPENF1_BASE_URL}/laps"
    rows = _expect_list(
        _get_json(lap_endpoint, params={"session_key": resolved.session_key}, source=OPENF1_SOURCE),
        source=OPENF1_SOURCE,
    )

    warnings: list[str] = []
    telemetry: list[RawSessionTelemetry] = []
    for row in rows:
        driver_number = _optional_int(row.get("driver_number"))
        driver_code = _driver_code_from_openf1_row(row, driver_map.get(driver_number))
        lap_number = _optional_int(row.get("lap_number"))
        if lap_number is None:
            warnings.append(f"Skipped OpenF1 telemetry row for {driver_code}: missing lap_number.")
            continue
        telemetry.append(
            RawSessionTelemetry(
                season=resolved.year,
                round=resolved.round_number,
                grand_prix=resolved.grand_prix,
                session=resolved.session_code,
                driver_code=driver_code,
                lap_number=lap_number,
                speed_i1_kph=_optional_int(row.get("speed_i1")),
                speed_i2_kph=_optional_int(row.get("speed_i2")),
                speed_fl_kph=_optional_int(row.get("speed_fl")),
                speed_st_kph=_optional_int(row.get("speed_st")),
                tyre_life_laps=_optional_int(row.get("tyre_age_at_start"))
                or _optional_int(row.get("lap_number")),
                track_status=_optional_string(row.get("track_status")),
                is_pit_out_lap=_optional_bool(row.get("is_pit_out_lap")),
                is_pit_in_lap=_optional_bool(row.get("is_pit_in_lap")),
                source=OPENF1_SOURCE,
                ingested_at=fetched_at,
            )
        )

    if not telemetry:
        raise RuntimeError("OpenF1 telemetry detail returned no rows for this session.")

    metadata = SourceMetadata(
        source=OPENF1_SOURCE,
        fetched_at=fetched_at,
        requested_year=request.year,
        requested_grand_prix=_stringify(request.grand_prix),
        requested_session=request.session,
        resolved_year=resolved.year,
        resolved_round=resolved.round_number,
        resolved_grand_prix=resolved.grand_prix,
        resolved_session=resolved.session_code,
        upstream_endpoints=[
            _render_endpoint(lap_endpoint, {"session_key": resolved.session_key}),
            driver_endpoint,
        ],
        warnings=warnings,
        result_row_count=0,
        lap_row_count=0,
        telemetry_row_count=len(telemetry),
    )
    return TelemetryPayload(telemetry=telemetry, metadata=metadata)


def _jolpica_results_payload(*, request: SourceRequest, fetched_at: str) -> SessionPayload:
    year, grand_prix, session = _require_context(request)
    resolved = _resolve_jolpica_round(year=year, grand_prix=grand_prix)
    dataset = SESSION_CODE_TO_JOLPICA_DATASET.get(session)
    if dataset is None:
        raise ValueError(
            "Jolpica session ingestion currently supports only Q, S, and R session codes."
        )

    endpoint = f"{JOLPICA_BASE_URL}/{year}/{resolved.round_number}/{dataset}/"
    payload = _get_json(endpoint, source=JOLPICA_SOURCE)
    rows = _extract_jolpica_result_rows(payload, dataset=dataset)
    warnings: list[str] = []
    records: list[RawSessionResult] = []
    for index, row in enumerate(rows):
        driver = _as_mapping(row.get("Driver"))
        driver_code = _driver_code_from_jolpica(driver, fallback=row.get("driverId"))
        position = _coalesce_position(
            row.get("position") or row.get("positionText"),
            fallback_index=index,
            warnings=warnings,
            provider=JOLPICA_SOURCE,
            driver_code=driver_code,
        )
        lap_time_ms = _jolpica_result_time_ms(row)
        records.append(
            RawSessionResult(
                season=resolved.year,
                round=resolved.round_number,
                session=session,
                driver_code=driver_code,
                position=position,
                lap_time_ms=lap_time_ms,
                source=JOLPICA_SOURCE,
                ingested_at=fetched_at,
            )
        )

    if not records:
        raise RuntimeError("Jolpica returned no usable rows for this session.")

    metadata = SourceMetadata(
        source=JOLPICA_SOURCE,
        fetched_at=fetched_at,
        requested_year=request.year,
        requested_grand_prix=_stringify(request.grand_prix),
        requested_session=request.session,
        resolved_year=resolved.year,
        resolved_round=resolved.round_number,
        resolved_grand_prix=resolved.grand_prix,
        resolved_session=session,
        upstream_endpoints=[endpoint],
        warnings=warnings,
        result_row_count=len(records),
        lap_row_count=0,
    )
    return SessionPayload(results=records, metadata=metadata)


def _jolpica_laps_payload(*, request: SourceRequest, fetched_at: str) -> LapPayload:
    year, grand_prix, session = _require_context(request)
    if session != "R":
        raise ValueError("Jolpica lap ingestion currently supports only race sessions (R).")
    resolved = _resolve_jolpica_round(year=year, grand_prix=grand_prix)
    endpoint = f"{JOLPICA_BASE_URL}/{year}/{resolved.round_number}/laps/"
    payload = _get_json(endpoint, source=JOLPICA_SOURCE)
    races = _extract_jolpica_races(payload)

    warnings: list[str] = []
    records: list[RawSessionLap] = []
    for race in races:
        laps = race.get("Laps")
        for lap in _expect_list(laps, source=JOLPICA_SOURCE, label="laps"):
            lap_number = _optional_int(lap.get("number"))
            if lap_number is None:
                continue
            timings = _expect_list(lap.get("Timings"), source=JOLPICA_SOURCE, label="timings")
            for timing in timings:
                driver_code = _driver_code_from_jolpica(
                    {},
                    fallback=timing.get("driverId"),
                )
                records.append(
                    RawSessionLap(
                        season=resolved.year,
                        round=resolved.round_number,
                        grand_prix=resolved.grand_prix,
                        session=session,
                        driver_code=driver_code,
                        lap_number=lap_number,
                        lap_time_ms=_parse_optional_time_to_ms(timing.get("time")),
                        sector_1_ms=None,
                        sector_2_ms=None,
                        sector_3_ms=None,
                        compound=None,
                        stint=None,
                        is_personal_best=None,
                        source=JOLPICA_SOURCE,
                        ingested_at=fetched_at,
                    )
                )

    if not records:
        raise RuntimeError("Jolpica returned no usable lap rows for this session.")

    metadata = SourceMetadata(
        source=JOLPICA_SOURCE,
        fetched_at=fetched_at,
        requested_year=request.year,
        requested_grand_prix=_stringify(request.grand_prix),
        requested_session=request.session,
        resolved_year=resolved.year,
        resolved_round=resolved.round_number,
        resolved_grand_prix=resolved.grand_prix,
        resolved_session=session,
        upstream_endpoints=[endpoint],
        warnings=warnings,
        result_row_count=0,
        lap_row_count=len(records),
    )
    return LapPayload(laps=records, metadata=metadata)


def _jolpica_telemetry_payload(*, request: SourceRequest, fetched_at: str) -> TelemetryPayload:
    lap_payload = _jolpica_laps_payload(request=request, fetched_at=fetched_at)
    telemetry = [
        RawSessionTelemetry(
            season=lap.season,
            round=lap.round,
            grand_prix=lap.grand_prix,
            session=lap.session,
            driver_code=lap.driver_code,
            lap_number=lap.lap_number,
            speed_i1_kph=None,
            speed_i2_kph=None,
            speed_fl_kph=None,
            speed_st_kph=None,
            tyre_life_laps=None,
            track_status=None,
            is_pit_out_lap=None,
            is_pit_in_lap=None,
            source=lap.source,
            ingested_at=lap.ingested_at,
        )
        for lap in lap_payload.laps
    ]
    metadata = SourceMetadata(
        source=lap_payload.metadata.source,
        fetched_at=lap_payload.metadata.fetched_at,
        requested_year=lap_payload.metadata.requested_year,
        requested_grand_prix=lap_payload.metadata.requested_grand_prix,
        requested_session=lap_payload.metadata.requested_session,
        resolved_year=lap_payload.metadata.resolved_year,
        resolved_round=lap_payload.metadata.resolved_round,
        resolved_grand_prix=lap_payload.metadata.resolved_grand_prix,
        resolved_session=lap_payload.metadata.resolved_session,
        upstream_endpoints=lap_payload.metadata.upstream_endpoints,
        warnings=lap_payload.metadata.warnings
        + ["Jolpica does not expose telemetry metrics; telemetry fields were left null."],
        result_row_count=0,
        lap_row_count=0,
        telemetry_row_count=len(telemetry),
    )
    return TelemetryPayload(telemetry=telemetry, metadata=metadata)


def _load_fastf1_session(*, year: int, grand_prix: str | int, session: str) -> object:
    fastf1_module = globals().get("fastf1")
    if fastf1_module is None:
        try:
            import fastf1 as fastf1_module
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "FastF1 is not installed. Install it with `pip install fastf1` "
                "and re-run with --source fastf1."
            ) from exc

    try:
        session_obj = fastf1_module.get_session(year, grand_prix, session)
        session_obj.load()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "FastF1 session load failed. Check year, grand_prix, and session inputs."
        ) from exc
    return session_obj


def _resolve_openf1_session(
    *,
    year: int,
    grand_prix: str | int,
    session: str,
) -> ResolvedOpenF1Session:
    session_name = SESSION_CODE_TO_OPENF1_NAME.get(session)
    if session_name is None:
        raise ValueError(f"Unsupported OpenF1 session code: {session}")

    endpoint = f"{OPENF1_BASE_URL}/sessions"
    sessions = _expect_list(
        _get_json(
            endpoint,
            params={"year": year, "session_name": session_name},
            source=OPENF1_SOURCE,
        ),
        source=OPENF1_SOURCE,
    )
    if not sessions:
        raise RuntimeError("OpenF1 returned no sessions for the requested filters.")

    target = _match_openf1_session(sessions, grand_prix=grand_prix)
    grand_prix_name = _openf1_meeting_name(target)
    ordered_meetings = _sorted_openf1_meetings(sessions)
    round_number = _find_openf1_round_number(ordered_meetings, target)

    meeting_key = _require_int(target.get("meeting_key"), "meeting_key")
    session_key = _require_int(target.get("session_key"), "session_key")
    return ResolvedOpenF1Session(
        year=year,
        round_number=round_number,
        grand_prix=grand_prix_name,
        session_code=session,
        session_key=session_key,
        meeting_key=meeting_key,
    )


def _match_openf1_session(
    sessions: Sequence[Mapping[str, object]],
    *,
    grand_prix: str | int,
) -> Mapping[str, object]:
    meetings = _sorted_openf1_meetings(sessions)
    if isinstance(grand_prix, int) or str(grand_prix).isdigit():
        round_number = int(grand_prix)
        if round_number <= 0 or round_number > len(meetings):
            raise ValueError(f"OpenF1 could not resolve round {grand_prix} for the requested year.")
        meeting_key = meetings[round_number - 1]
        return next(
            session
            for session in sessions
            if _require_int(session.get("meeting_key"), "meeting_key") == meeting_key
        )

    needle = _normalize_lookup(str(grand_prix))
    for session in sessions:
        haystack = " ".join(
            [
                _stringify(session.get("country_name")) or "",
                _stringify(session.get("location")) or "",
                _stringify(session.get("circuit_short_name")) or "",
                _stringify(session.get("meeting_name")) or "",
                _stringify(session.get("meeting_official_name")) or "",
            ]
        )
        if needle in _normalize_lookup(haystack):
            return session
    raise ValueError(f"OpenF1 could not resolve grand prix '{grand_prix}'.")


def _openf1_driver_map(session_key: int) -> tuple[dict[int, Mapping[str, object]], str]:
    endpoint = f"{OPENF1_BASE_URL}/drivers"
    payload = _expect_list(
        _get_json(endpoint, params={"session_key": session_key}, source=OPENF1_SOURCE),
        source=OPENF1_SOURCE,
    )
    mapping: dict[int, Mapping[str, object]] = {}
    for row in payload:
        driver_number = _optional_int(row.get("driver_number"))
        if driver_number is not None:
            mapping[driver_number] = row
    return mapping, _render_endpoint(endpoint, {"session_key": session_key})


def _openf1_best_lap_times(rows: object) -> dict[int, int]:
    best: dict[int, int] = {}
    for row in _expect_list(rows, source=OPENF1_SOURCE):
        driver_number = _optional_int(row.get("driver_number"))
        if driver_number is None:
            continue
        lap_time_ms = _parse_optional_time_to_ms(row.get("lap_duration"))
        if lap_time_ms is None:
            continue
        current = best.get(driver_number)
        if current is None or lap_time_ms < current:
            best[driver_number] = lap_time_ms
    return best


def _driver_code_from_openf1_row(
    row: Mapping[str, object],
    driver: Mapping[str, object] | None,
) -> str:
    for candidate in (
        row.get("name_acronym"),
        (driver or {}).get("name_acronym"),
        row.get("driver_code"),
    ):
        code = _optional_string(candidate)
        if code:
            return code.upper()
    full_name = _optional_string((driver or {}).get("full_name")) or _optional_string(
        row.get("full_name")
    )
    if full_name:
        return _derive_driver_code_from_name(full_name)
    raise ValueError("OpenF1 driver row is missing a usable driver code.")


def _resolve_jolpica_round(*, year: int, grand_prix: str | int) -> ResolvedJolpicaRound:
    if isinstance(grand_prix, int) or str(grand_prix).isdigit():
        round_number = int(grand_prix)
        race = _fetch_jolpica_race(year=year, round_number=round_number)
        return ResolvedJolpicaRound(
            year=year,
            round_number=round_number,
            grand_prix=_stringify(race.get("raceName")) or f"Round {round_number}",
        )

    races = _fetch_jolpica_races(year=year)
    needle = _normalize_lookup(str(grand_prix))
    for race in races:
        haystack = " ".join(
            [
                _stringify(race.get("raceName")) or "",
                _stringify(_as_mapping(race.get("Circuit")).get("circuitName")) or "",
                _stringify(
                    _as_mapping(_as_mapping(race.get("Circuit")).get("Location")).get("country")
                )
                or "",
                _stringify(
                    _as_mapping(_as_mapping(race.get("Circuit")).get("Location")).get("locality")
                )
                or "",
            ]
        )
        if needle in _normalize_lookup(haystack):
            return ResolvedJolpicaRound(
                year=year,
                round_number=_require_int(race.get("round"), "round"),
                grand_prix=_stringify(race.get("raceName")) or str(grand_prix),
            )
    raise ValueError(f"Jolpica could not resolve grand prix '{grand_prix}'.")


def _fetch_jolpica_races(*, year: int) -> list[Mapping[str, object]]:
    endpoint = f"{JOLPICA_BASE_URL}/{year}/races/"
    return _extract_jolpica_races(_get_json(endpoint, source=JOLPICA_SOURCE))


def _fetch_jolpica_race(*, year: int, round_number: int) -> Mapping[str, object]:
    endpoint = f"{JOLPICA_BASE_URL}/{year}/{round_number}/races/"
    races = _extract_jolpica_races(_get_json(endpoint, source=JOLPICA_SOURCE))
    if not races:
        raise RuntimeError("Jolpica returned no race metadata for the requested round.")
    return races[0]


def _extract_jolpica_races(payload: object) -> list[Mapping[str, object]]:
    mapping = _as_mapping(payload)
    mr_data = _as_mapping(mapping.get("MRData"))
    race_table = _as_mapping(mr_data.get("RaceTable"))
    races = race_table.get("Races")
    return _expect_list(races, source=JOLPICA_SOURCE, label="races")


def _extract_jolpica_result_rows(payload: object, *, dataset: str) -> list[Mapping[str, object]]:
    races = _extract_jolpica_races(payload)
    if not races:
        return []
    race = races[0]
    key = {
        "results": "Results",
        "qualifying": "QualifyingResults",
        "sprint": "SprintResults",
    }[dataset]
    return _expect_list(race.get(key), source=JOLPICA_SOURCE, label=key)


def _jolpica_result_time_ms(row: Mapping[str, object]) -> int:
    for candidate in (
        _dig(row, "FastestLap", "Time", "time"),
        _dig(row, "Time", "time"),
        row.get("Q3"),
        row.get("Q2"),
        row.get("Q1"),
    ):
        parsed = _parse_optional_time_to_ms(candidate)
        if parsed is not None:
            return parsed
    return 0


def _driver_code_from_jolpica(driver: Mapping[str, object], *, fallback: object) -> str:
    for candidate in (driver.get("code"), fallback, driver.get("driverId")):
        code = _optional_string(candidate)
        if code:
            return code.upper()[:3] if len(code) > 3 and code.isalpha() else code.upper()
    family_name = _optional_string(driver.get("familyName"))
    given_name = _optional_string(driver.get("givenName"))
    if family_name or given_name:
        return _derive_driver_code_from_name(
            " ".join(part for part in [given_name, family_name] if part)
        )
    raise ValueError("Jolpica driver row is missing a usable driver code.")


def map_fastf1_results(
    *,
    season: int,
    round_number: int,
    session: str,
    results: Sequence[Mapping[str, object]],
    ingested_at: str,
) -> list[RawSessionResult]:
    mapped: list[RawSessionResult] = []

    for index, row in enumerate(results):
        driver_code = _fastf1_driver_code(row, index=index)
        position = _require_int(row.get("Position"), "Position", index=index)
        lap_time_ms = _parse_time_to_ms(row.get("Time"))

        mapped.append(
            RawSessionResult(
                season=season,
                round=round_number,
                session=session,
                driver_code=driver_code,
                position=position,
                lap_time_ms=lap_time_ms,
                source=FASTF1_SOURCE,
                ingested_at=ingested_at,
            )
        )

    return mapped


def map_fastf1_laps(
    *,
    season: int,
    round_number: int,
    grand_prix: str,
    session: str,
    laps: Sequence[Mapping[str, object]],
    ingested_at: str,
) -> list[RawSessionLap]:
    mapped: list[RawSessionLap] = []

    for index, row in enumerate(laps):
        driver_code = _fastf1_driver_code(row, index=index)
        lap_number = _require_int(row.get("LapNumber"), "LapNumber", index=index)
        compound = _optional_string(row.get("Compound"))
        stint = _optional_int(row.get("Stint"))
        is_personal_best = _optional_bool(row.get("IsPersonalBest"))

        mapped.append(
            RawSessionLap(
                season=season,
                round=round_number,
                grand_prix=grand_prix,
                session=session,
                driver_code=driver_code,
                lap_number=lap_number,
                lap_time_ms=_parse_optional_time_to_ms(row.get("LapTime")),
                sector_1_ms=_parse_optional_time_to_ms(row.get("Sector1Time")),
                sector_2_ms=_parse_optional_time_to_ms(row.get("Sector2Time")),
                sector_3_ms=_parse_optional_time_to_ms(row.get("Sector3Time")),
                compound=compound,
                stint=stint,
                is_personal_best=is_personal_best,
                source=FASTF1_SOURCE,
                ingested_at=ingested_at,
            )
        )

    return mapped


def map_fastf1_telemetry(
    *,
    season: int,
    round_number: int,
    grand_prix: str,
    session: str,
    laps: Sequence[Mapping[str, object]],
    ingested_at: str,
) -> list[RawSessionTelemetry]:
    telemetry: list[RawSessionTelemetry] = []

    for index, row in enumerate(laps):
        driver_code = _fastf1_driver_code(row, index=index)
        lap_number = _require_int(row.get("LapNumber"), "LapNumber", index=index)
        telemetry.append(
            RawSessionTelemetry(
                season=season,
                round=round_number,
                grand_prix=grand_prix,
                session=session,
                driver_code=driver_code,
                lap_number=lap_number,
                speed_i1_kph=_optional_int(row.get("SpeedI1")),
                speed_i2_kph=_optional_int(row.get("SpeedI2")),
                speed_fl_kph=_optional_int(row.get("SpeedFL")),
                speed_st_kph=_optional_int(row.get("SpeedST")),
                tyre_life_laps=_optional_int(row.get("TyreLife")),
                track_status=_optional_string(row.get("TrackStatus")),
                is_pit_out_lap=_optional_bool(row.get("PitOutTime") is not None),
                is_pit_in_lap=_optional_bool(row.get("PitInTime") is not None),
                source=FASTF1_SOURCE,
                ingested_at=ingested_at,
            )
        )

    return telemetry


def _get_json(
    url: str,
    *,
    params: Mapping[str, object] | None = None,
    source: str,
) -> object:
    try:
        with httpx.Client(
            timeout=DEFAULT_HTTP_TIMEOUT_SECONDS,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            follow_redirects=True,
        ) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"{source} request failed: {url}") from exc


def _records_from_frame_like(results: object) -> Sequence[Mapping[str, object]]:
    if isinstance(results, list):
        return results

    to_dict = getattr(results, "to_dict", None)
    if callable(to_dict):
        return to_dict("records")

    raise TypeError("FastF1 results object must be a list of dicts or a pandas DataFrame.")


def _require_context(request: SourceRequest) -> tuple[int, str | int, str]:
    if request.year is None or request.grand_prix is None or request.session is None:
        raise ValueError("year, grand_prix, and session are required for source ingestion")
    return request.year, request.grand_prix, request.session


def _require_driver_code(value: object, *, index: int) -> str:
    if value is None:
        raise ValueError(f"Driver code is required (row {index})")
    driver = str(value).strip()
    if not driver:
        raise ValueError(f"Driver code is required (row {index})")
    return driver


def _fastf1_driver_code(row: Mapping[str, object], *, index: int) -> str:
    for key in ("Driver", "Abbreviation", "DriverCode", "DriverId"):
        value = _optional_string(row.get(key))
        if value:
            if key == "DriverId" and len(value) > 3:
                return _derive_driver_code_from_name(value.replace("_", " "))
            return value.upper()

    full_name = _optional_string(row.get("FullName"))
    if full_name:
        return _derive_driver_code_from_name(full_name)

    available = ", ".join(sorted(str(key) for key in row.keys())) or "none"
    raise ValueError(
        f"Driver code is required (row {index}); "
        "expected one of Driver, Abbreviation, DriverCode, DriverId, or FullName. "
        f"Available columns: {available}"
    )


def _require_int(value: object, label: str, *, index: int | None = None) -> int:
    if value is None:
        if index is None:
            raise ValueError(f"{label} is required")
        raise ValueError(f"{label} is required (row {index})")
    return int(value)


def _coalesce_position(
    value: object,
    *,
    fallback_index: int,
    warnings: list[str],
    provider: str,
    driver_code: str,
) -> int:
    parsed = _optional_int(value)
    if parsed is not None and parsed > 0:
        return parsed
    fallback = fallback_index + 1
    warnings.append(
        f"{provider} row for {driver_code} was missing a numeric position; "
        f"used fallback rank {fallback}."
    )
    return fallback


def _parse_time_to_ms(value: object) -> int:
    parsed = _parse_optional_time_to_ms(value)
    return parsed or 0


def _parse_optional_time_to_ms(value: object) -> int | None:
    if value is None:
        return None

    total_seconds = getattr(value, "total_seconds", None)
    if callable(total_seconds):
        seconds = float(total_seconds())
        if not isfinite(seconds) or seconds <= 0:
            return None
        return int(round(seconds * 1000))

    if isinstance(value, (int, float)):
        numeric = float(value)
        if not isfinite(numeric) or numeric <= 0:
            return None
        return int(round(numeric * 1000))

    text = str(value).strip()
    if not text or text.lower() in {"nat", "none", "null"}:
        return None

    parts = text.split(":")
    try:
        if len(parts) == 1:
            seconds = float(parts[0])
        elif len(parts) == 2:
            minutes = float(parts[0])
            seconds = minutes * 60 + float(parts[1])
        elif len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = hours * 3600 + minutes * 60 + float(parts[2])
        else:
            return None
    except ValueError:
        return None
    if seconds <= 0:
        return None
    return int(round(seconds * 1000))


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _optional_bool(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _resolve_event_name(event: object, fallback: str | int) -> str:
    if isinstance(event, Mapping):
        for key in ("EventName", "OfficialEventName", "Event"):
            value = event.get(key)
            if value:
                return str(value)
    return str(fallback)


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _dig(mapping: Mapping[str, object], *path: str) -> object:
    current: object = mapping
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _expect_list(
    value: object,
    *,
    source: str,
    label: str = "payload",
) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise RuntimeError(f"{source} {label} was not returned as a list.")
    output: list[Mapping[str, object]] = []
    for item in value:
        if isinstance(item, Mapping):
            output.append(item)
    return output


def _normalize_lookup(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").split())


def _stringify(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _derive_driver_code_from_name(name: str) -> str:
    parts = [part for part in name.replace("-", " ").split() if part]
    if not parts:
        raise ValueError("Unable to derive driver code from an empty name.")
    family = parts[-1].upper()
    return family[:3]


def _render_endpoint(endpoint: str, params: Mapping[str, object] | None = None) -> str:
    if not params:
        return endpoint
    query = "&".join(f"{key}={value}" for key, value in params.items())
    return f"{endpoint}?{query}"


def _sorted_openf1_meetings(sessions: Sequence[Mapping[str, object]]) -> list[int]:
    keyed: dict[int, str] = {}
    for session in sessions:
        meeting_key = _require_int(session.get("meeting_key"), "meeting_key")
        keyed[meeting_key] = _stringify(session.get("date_start")) or ""
    return [key for key, _ in sorted(keyed.items(), key=lambda item: item[1])]


def _find_openf1_round_number(meeting_keys: Sequence[int], session: Mapping[str, object]) -> int:
    meeting_key = _require_int(session.get("meeting_key"), "meeting_key")
    for index, key in enumerate(meeting_keys, start=1):
        if key == meeting_key:
            return index
    return 0


def _openf1_meeting_name(session: Mapping[str, object]) -> str:
    for key in ("meeting_name", "meeting_official_name", "country_name", "location"):
        value = _optional_string(session.get(key))
        if value:
            return value
    return "Unknown Grand Prix"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
