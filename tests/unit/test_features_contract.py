from pathlib import Path

import pytest

from f1_features.contracts import FEATURE_SESSION_RESULTS_COLUMNS


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
