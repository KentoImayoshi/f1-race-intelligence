from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/processing/src"))

from f1_processing.contracts import PROCESSED_SESSION_RESULTS_COLUMNS  # noqa: E402


@pytest.mark.unit
def test_processed_contract_columns() -> None:
    assert PROCESSED_SESSION_RESULTS_COLUMNS == [
        "season",
        "round",
        "session",
        "driver_code",
        "position",
        "lap_time_ms",
        "processed_at",
    ]
