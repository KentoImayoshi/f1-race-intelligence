"""Ingestion entrypoints for raw Formula 1 session data."""

from __future__ import annotations

import logging
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from f1_ingestion.contracts import RawSessionLap, RawSessionResult, RawSessionTelemetry
from f1_ingestion.metadata import write_metadata_sidecar
from f1_ingestion.sources import (
    FASTF1_SOURCE,
    JOLPICA_SOURCE,
    OPENF1_SOURCE,
    SEED_SOURCE,
    SourceRequest,
    _parse_optional_time_to_ms,
    _parse_time_to_ms,
    _records_from_frame_like,
    _require_driver_code,
    _require_int,
    _resolve_event_name,
    load_lap_payload,
    load_session_payload,
    load_telemetry_payload,
    map_fastf1_laps,
    map_fastf1_results,
    map_fastf1_telemetry,
    utc_now,
)

logger = logging.getLogger("f1_ingestion")

SUPPORTED_RESULT_SOURCES = {
    SEED_SOURCE,
    FASTF1_SOURCE,
    OPENF1_SOURCE,
    JOLPICA_SOURCE,
    "auto",
}
SUPPORTED_LAP_SOURCES = {
    SEED_SOURCE,
    FASTF1_SOURCE,
    OPENF1_SOURCE,
    JOLPICA_SOURCE,
    "auto",
}
SUPPORTED_TELEMETRY_SOURCES = {
    SEED_SOURCE,
    FASTF1_SOURCE,
    OPENF1_SOURCE,
    JOLPICA_SOURCE,
    "auto",
}
AUTO_RESULT_SOURCE_ORDER = [FASTF1_SOURCE, OPENF1_SOURCE, JOLPICA_SOURCE]
AUTO_LAP_SOURCE_ORDER = [FASTF1_SOURCE, OPENF1_SOURCE, JOLPICA_SOURCE]
AUTO_TELEMETRY_SOURCE_ORDER = [FASTF1_SOURCE, OPENF1_SOURCE, JOLPICA_SOURCE]


def ingest_raw_session_results(
    output_dir: Path,
    source: str = SEED_SOURCE,
    *,
    year: int | None = None,
    grand_prix: str | int | None = None,
    session: str | None = None,
) -> Path:
    """Write a raw session results parquet file to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ingested_at = utc_now()
    payload = _load_results_with_auto_fallback(
        source=source,
        year=year,
        grand_prix=grand_prix,
        session=session,
        ingested_at=ingested_at,
    )

    table = pa.Table.from_pylist(
        [record.to_record() for record in payload.results],
        schema=_result_schema(),
    )
    output_path = output_dir / "raw_session_results.parquet"

    logger.info(
        "writing raw session results",
        extra={
            "rows": table.num_rows,
            "path": str(output_path),
            "source": payload.metadata.source,
            "round": payload.metadata.resolved_round,
            "session": payload.metadata.resolved_session,
        },
    )
    pq.write_table(table, output_path)
    write_metadata_sidecar(output_path, payload.metadata.to_dict())

    return output_path


def ingest_raw_session_laps(
    output_dir: Path,
    source: str = FASTF1_SOURCE,
    *,
    year: int | None = None,
    grand_prix: str | int | None = None,
    session: str | None = None,
) -> Path:
    """Write a raw session laps parquet file to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ingested_at = utc_now()
    payload = _load_laps_with_auto_fallback(
        source=source,
        year=year,
        grand_prix=grand_prix,
        session=session,
        ingested_at=ingested_at,
    )

    table = pa.Table.from_pylist(
        [record.to_record() for record in payload.laps],
        schema=_laps_schema(),
    )
    output_path = output_dir / "raw_session_laps.parquet"

    logger.info(
        "writing raw session laps",
        extra={
            "rows": table.num_rows,
            "path": str(output_path),
            "source": payload.metadata.source,
            "round": payload.metadata.resolved_round,
            "session": payload.metadata.resolved_session,
        },
    )
    pq.write_table(table, output_path)
    write_metadata_sidecar(output_path, payload.metadata.to_dict())

    return output_path


def ingest_raw_session_telemetry(
    output_dir: Path,
    source: str = FASTF1_SOURCE,
    *,
    year: int | None = None,
    grand_prix: str | int | None = None,
    session: str | None = None,
) -> Path:
    """Write a raw session telemetry/detail parquet file to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ingested_at = utc_now()
    payload = _load_telemetry_with_auto_fallback(
        source=source,
        year=year,
        grand_prix=grand_prix,
        session=session,
        ingested_at=ingested_at,
    )

    table = pa.Table.from_pylist(
        [record.to_record() for record in payload.telemetry],
        schema=_telemetry_schema(),
    )
    output_path = output_dir / "raw_session_telemetry.parquet"

    logger.info(
        "writing raw session telemetry",
        extra={
            "rows": table.num_rows,
            "path": str(output_path),
            "source": payload.metadata.source,
            "round": payload.metadata.resolved_round,
            "session": payload.metadata.resolved_session,
        },
    )
    pq.write_table(table, output_path)
    write_metadata_sidecar(output_path, payload.metadata.to_dict())

    return output_path


def _load_results_with_auto_fallback(
    *,
    source: str,
    year: int | None,
    grand_prix: str | int | None,
    session: str | None,
    ingested_at: str,
):
    if source == "auto":
        return _attempt_sources(
            ordered_sources=AUTO_RESULT_SOURCE_ORDER,
            year=year,
            grand_prix=grand_prix,
            session=session,
            ingested_at=ingested_at,
            loader=load_session_payload,
            context="results",
        )
    if source not in SUPPORTED_RESULT_SOURCES:
        raise ValueError(f"Unknown ingestion source: {source}")
    return load_session_payload(
        SourceRequest(
            source=source,
            year=year,
            grand_prix=grand_prix,
            session=session,
        ),
        fetched_at=ingested_at,
    )


def _load_laps_with_auto_fallback(
    *,
    source: str,
    year: int | None,
    grand_prix: str | int | None,
    session: str | None,
    ingested_at: str,
):
    if source == "auto":
        return _attempt_sources(
            ordered_sources=AUTO_LAP_SOURCE_ORDER,
            year=year,
            grand_prix=grand_prix,
            session=session,
            ingested_at=ingested_at,
            loader=load_lap_payload,
            context="laps",
        )
    if source not in SUPPORTED_LAP_SOURCES:
        raise ValueError(
            "Lap-level raw ingestion currently supports only the "
            "fastf1, openf1, and jolpica sources"
        )
    return load_lap_payload(
        SourceRequest(
            source=source,
            year=year,
            grand_prix=grand_prix,
            session=session,
        ),
        fetched_at=ingested_at,
    )


def _load_telemetry_with_auto_fallback(
    *,
    source: str,
    year: int | None,
    grand_prix: str | int | None,
    session: str | None,
    ingested_at: str,
):
    if source == "auto":
        return _attempt_sources(
            ordered_sources=AUTO_TELEMETRY_SOURCE_ORDER,
            year=year,
            grand_prix=grand_prix,
            session=session,
            ingested_at=ingested_at,
            loader=load_telemetry_payload,
            context="telemetry",
        )
    if source not in SUPPORTED_TELEMETRY_SOURCES:
        raise ValueError(
            "Telemetry raw ingestion currently supports only the "
            "seed, fastf1, openf1, and jolpica sources"
        )
    return load_telemetry_payload(
        SourceRequest(
            source=source,
            year=year,
            grand_prix=grand_prix,
            session=session,
        ),
        fetched_at=ingested_at,
    )


def _attempt_sources(
    *,
    ordered_sources: list[str],
    year: int | None,
    grand_prix: str | int | None,
    session: str | None,
    ingested_at: str,
    loader,
    context: str,
):
    failures: list[str] = []
    for candidate in ordered_sources:
        try:
            return loader(
                SourceRequest(
                    source=candidate,
                    year=year,
                    grand_prix=grand_prix,
                    session=session,
                ),
                fetched_at=ingested_at,
            )
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{candidate}: {exc}")
            logger.warning(
                "ingestion source fallback",
                extra={"source": candidate, "context": context},
            )
    joined = "; ".join(failures) if failures else "no sources were attempted"
    raise RuntimeError(f"All auto-ingestion sources failed for {context}: {joined}")


def _records_from_results(results: object):
    return _records_from_frame_like(results)


def _result_schema() -> pa.Schema:
    return pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("position", pa.int64()),
            ("lap_time_ms", pa.int64()),
            ("source", pa.string()),
            ("ingested_at", pa.string()),
        ]
    )


def _laps_schema() -> pa.Schema:
    return pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("grand_prix", pa.string()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("lap_number", pa.int64()),
            ("lap_time_ms", pa.int64()),
            ("sector_1_ms", pa.int64()),
            ("sector_2_ms", pa.int64()),
            ("sector_3_ms", pa.int64()),
            ("compound", pa.string()),
            ("stint", pa.int64()),
            ("is_personal_best", pa.bool_()),
            ("source", pa.string()),
            ("ingested_at", pa.string()),
        ]
    )


def _telemetry_schema() -> pa.Schema:
    return pa.schema(
        [
            ("season", pa.int64()),
            ("round", pa.int64()),
            ("grand_prix", pa.string()),
            ("session", pa.string()),
            ("driver_code", pa.string()),
            ("lap_number", pa.int64()),
            ("speed_i1_kph", pa.int64()),
            ("speed_i2_kph", pa.int64()),
            ("speed_fl_kph", pa.int64()),
            ("speed_st_kph", pa.int64()),
            ("tyre_life_laps", pa.int64()),
            ("track_status", pa.string()),
            ("is_pit_out_lap", pa.bool_()),
            ("is_pit_in_lap", pa.bool_()),
            ("source", pa.string()),
            ("ingested_at", pa.string()),
        ]
    )


__all__ = [
    "RawSessionLap",
    "RawSessionResult",
    "RawSessionTelemetry",
    "ingest_raw_session_laps",
    "ingest_raw_session_telemetry",
    "ingest_raw_session_results",
    "map_fastf1_laps",
    "map_fastf1_results",
    "map_fastf1_telemetry",
    "_parse_optional_time_to_ms",
    "_parse_time_to_ms",
    "_records_from_results",
    "_records_from_frame_like",
    "_require_driver_code",
    "_require_int",
    "_resolve_event_name",
]
