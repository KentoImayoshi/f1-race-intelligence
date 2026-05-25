"""CLI entrypoint for ingestion."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from f1_ingestion.ingestion import (
    FASTF1_SOURCE,
    JOLPICA_SOURCE,
    OPENF1_SOURCE,
    SEED_SOURCE,
    ingest_raw_session_laps,
    ingest_raw_session_results,
    ingest_raw_session_telemetry,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run minimal raw data ingestion.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory to write raw parquet artifacts.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default="seed",
        choices=[SEED_SOURCE, FASTF1_SOURCE, OPENF1_SOURCE, JOLPICA_SOURCE, "auto"],
        help="Ingestion source.",
    )
    parser.add_argument("--year", type=int, help="F1 season year (fastf1 only).")
    parser.add_argument(
        "--grand-prix",
        type=str,
        help="Grand Prix name or round number (fastf1 only).",
    )
    parser.add_argument(
        "--session",
        type=str,
        help="Session code, e.g. R, Q, FP1 (fastf1 only).",
    )
    parser.add_argument(
        "--include-laps",
        action="store_true",
        help="Also fetch raw lap-level parquet when supported by the selected source.",
    )
    parser.add_argument(
        "--include-telemetry",
        action="store_true",
        help="Also fetch raw telemetry/detail parquet when supported by the selected source.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = _parse_args()

    output_path = ingest_raw_session_results(
        output_dir=args.output_dir,
        source=args.source,
        year=args.year,
        grand_prix=args.grand_prix,
        session=args.session,
    )
    print(f"Wrote {output_path}")
    if args.include_laps:
        laps_path = ingest_raw_session_laps(
            output_dir=args.output_dir,
            source=args.source,
            year=args.year,
            grand_prix=args.grand_prix,
            session=args.session,
        )
        print(f"Wrote {laps_path}")
    if args.include_telemetry:
        telemetry_path = ingest_raw_session_telemetry(
            output_dir=args.output_dir,
            source=args.source,
            year=args.year,
            grand_prix=args.grand_prix,
            session=args.session,
        )
        print(f"Wrote {telemetry_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
