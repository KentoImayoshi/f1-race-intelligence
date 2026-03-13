"""Minimal ingestion slice for raw Formula 1 session results."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from f1_ingestion.contracts import RAW_SESSION_RESULTS_COLUMNS, RawSessionResult

logger = logging.getLogger("f1_ingestion")


def ingest_raw_session_results(output_dir: Path, source: str = "seed") -> Path:
    """Write a raw session results parquet file to the output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    ingested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    records = [record.to_record() for record in _load_session_results(source, ingested_at)]

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


def _load_session_results(source: str, ingested_at: str) -> list[RawSessionResult]:
    if source == "seed":
        return _seed_session_results(ingested_at)
    if source == "fastf1":
        return _fastf1_session_results(ingested_at)

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


def _fastf1_session_results(ingested_at: str) -> list[RawSessionResult]:
    try:
        import fastf1  # noqa: F401
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "FastF1 is not installed. Install it with `pip install fastf1` "
            "and re-run with --source fastf1."
        ) from exc

    raise RuntimeError("FastF1 ingestion is not implemented yet.")
