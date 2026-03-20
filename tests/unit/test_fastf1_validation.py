import pytest
from f1_ingestion.ingestion import map_fastf1_results


@pytest.mark.unit
def test_map_fastf1_requires_position() -> None:
    records = [{"Driver": "VER", "Position": None, "Time": "1:32.123"}]

    with pytest.raises(ValueError, match=r"Position is required \(row 0\)"):
        map_fastf1_results(
            season=2024,
            round_number=1,
            session="R",
            results=records,
            ingested_at="2026-03-13T00:00:00Z",
        )


@pytest.mark.unit
def test_map_fastf1_rejects_empty_driver_code() -> None:
    records = [{"Driver": "   ", "Position": 1, "Time": "1:32.123"}]

    with pytest.raises(ValueError, match=r"Driver code is required \(row 0\)"):
        map_fastf1_results(
            season=2024,
            round_number=1,
            session="R",
            results=records,
            ingested_at="2026-03-13T00:00:00Z",
        )
