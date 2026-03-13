"""CLI entrypoint for ingestion."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from f1_ingestion.ingestion import ingest_raw_session_results


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
        help="Ingestion source (seed or fastf1).",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = _parse_args()

    output_path = ingest_raw_session_results(output_dir=args.output_dir, source=args.source)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
