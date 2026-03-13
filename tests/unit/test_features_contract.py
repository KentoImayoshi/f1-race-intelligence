import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/features/src"))

from f1_features.contracts import FEATURE_SESSION_RESULTS_COLUMNS  # noqa: E402


@pytest.mark.unit
def test_feature_contract_columns() -> None:
    assert FEATURE_SESSION_RESULTS_COLUMNS == [
        "season",
        "round",
        "session",
        "driver_code",
        "position",
        "lap_time_ms",
        "has_lap_time",
        "lap_time_seconds",
        "position_numeric",
        "feature_generated_at",
    ]
