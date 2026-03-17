from pathlib import Path

import pytest

from f1_insights.contracts import INSIGHT_SESSION_TOP_DRIVERS_COLUMNS


@pytest.mark.unit
def test_insights_contract_columns() -> None:
    assert INSIGHT_SESSION_TOP_DRIVERS_COLUMNS == [
        "season",
        "round",
        "session",
        "rank",
        "driver_code",
        "score",
        "insight_generated_at",
    ]
