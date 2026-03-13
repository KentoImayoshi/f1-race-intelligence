import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "packages/insights/src"))

from f1_insights.contracts import INSIGHT_SESSION_TOP_DRIVERS_COLUMNS  # noqa: E402


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
