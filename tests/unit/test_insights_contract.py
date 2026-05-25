import pytest
from f1_insights.contracts import (
    INSIGHT_SESSION_TOP_DRIVERS_COLUMNS,
    INTELLIGENCE_DRIVER_REPORT_COLUMNS,
    INTELLIGENCE_RACE_TREND_COLUMNS,
    INTELLIGENCE_SESSION_SUMMARY_COLUMNS,
)


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


@pytest.mark.unit
def test_race_intelligence_contract_columns() -> None:
    assert INTELLIGENCE_SESSION_SUMMARY_COLUMNS[:5] == [
        "season",
        "round",
        "grand_prix",
        "session",
        "summary_type",
    ]
    assert "performance_summary" in INTELLIGENCE_DRIVER_REPORT_COLUMNS
    assert "trend_detail" in INTELLIGENCE_RACE_TREND_COLUMNS
