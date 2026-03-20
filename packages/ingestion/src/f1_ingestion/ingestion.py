"""Minimal ingestion slice for raw Formula 1 session results."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

import pyarrow as pa
import pyarrow.parquet as pq

from f1_ingestion.contracts import RawSessionResult

logger = logging.getLogger("f1_ingestion")


def ingest_raw_session_results(
    output_dir: Path,
    source: str = "seed",
    *,
    year: int | None = None,
    grand_prix: str | int | None = None,
    session: str | None = None,
) -> Path:
    """Write a raw session results parquet file to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    ingested_at = (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    records = [
        record.to_record()
        for record in _load_session_results(
            source, ingested_at, year=year, grand_prix=grand_prix, session=session
        )
    ]

    schema = pa.schema(
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

    table = pa.Table.from_pylist(records, schema=schema)
    output_path = output_dir / "raw_session_results.parquet"

    logger.info(
        "writing raw session results",
        extra={"rows": table.num_rows, "path": str(output_path), "source": source},
    )
    pq.write_table(table, output_path)

    return output_path


def _load_session_results(
    source: str,
    ingested_at: str,
    *,
    year: int | None,
    grand_prix: str | int | None,
    session: str | None,
) -> list[RawSessionResult]:
    if source == "seed":
        return _seed_session_results(ingested_at)
    if source == "fastf1":
        return _fastf1_session_results(
            ingested_at=ingested_at, year=year, grand_prix=grand_prix, session=session
        )

    raise ValueError(f"Unknown ingestion source: {source}")


def _seed_session_results(ingested_at: str) -> list[RawSessionResult]:
    return [
        RawSessionResult(
            season=2024,
            round=1,
            session="R",
            driver_code="VER",
            position=1,
            lap_time_ms=5361234,
            source="seed",
            ingested_at=ingested_at,
        ),
        RawSessionResult(
            season=2024,
            round=1,
            session="R",
            driver_code="PER",
            position=2,
            lap_time_ms=5369876,
            source="seed",
            ingested_at=ingested_at,
        ),
        RawSessionResult(
            season=2024,
            round=1,
            session="R",
            driver_code="LEC",
            position=3,
            lap_time_ms=5374321,
            source="seed",
            ingested_at=ingested_at,
        ),
    ]


def _fastf1_session_results(
    *, ingested_at: str, year: int | None, grand_prix: str | int | None, session: str | None
) -> list[RawSessionResult]:
    if year is None or grand_prix is None or session is None:
        raise ValueError("year, grand_prix, and session are required for fastf1 ingestion")

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

    results = getattr(session_obj, "results", None)
    if results is None:
        raise RuntimeError("FastF1 session results are unavailable for this session.")

    return map_fastf1_results(
        season=year,
        round_number=int(session_obj.event["RoundNumber"]),
        session=session,
        results=_records_from_results(results),
        ingested_at=ingested_at,
    )


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
        driver_code = _require_driver_code(row.get("Driver"), index=index)
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
                source="fastf1",
                ingested_at=ingested_at,
            )
        )

    return mapped


def _records_from_results(results: object) -> Sequence[Mapping[str, object]]:
    if isinstance(results, list):
        return results

    to_dict = getattr(results, "to_dict", None)
    if callable(to_dict):
        return to_dict("records")

    raise TypeError("FastF1 results object must be a list of dicts or a pandas DataFrame.")


def _require_driver_code(value: object, *, index: int) -> str:
    if value is None:
        raise ValueError(f"Driver code is required (row {index})")
    driver = str(value).strip()
    if not driver:
        raise ValueError(f"Driver code is required (row {index})")
    return driver


def _require_int(value: object, label: str, *, index: int) -> int:
    if value is None:
        raise ValueError(f"{label} is required (row {index})")
    return int(value)


def _parse_time_to_ms(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(float(value) * 1000)

    text = str(value).strip()
    if not text:
        return 0

    parts = text.split(":")
    if len(parts) == 1:
        seconds = float(parts[0])
    else:
        minutes = float(parts[0])
        seconds = float(parts[1])
        seconds = minutes * 60 + seconds

    return int(round(seconds * 1000))
