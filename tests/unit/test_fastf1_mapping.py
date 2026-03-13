import pytest

from f1_ingestion.ingestion import map_fastf1_results


@pytest.mark.unit
def test_map_fastf1_results_to_raw_contract() -> None:
    records = [
        {"Driver": "VER", "Position": 1, "Time": "1:32.123"},
        {"Driver": "PER", "Position": 2, "Time": "1:32.456"},
        {"Driver": "LEC", "Position": 3, "Time": None},
    ]

    results = map_fastf1_results(
        season=2024,
        round_number=1,
        session="R",
        results=records,
        ingested_at="2026-03-13T00:00:00Z",
    )

    assert [r.driver_code for r in results] == ["VER", "PER", "LEC"]
    assert [r.position for r in results] == [1, 2, 3]
    assert [r.lap_time_ms for r in results] == [92123, 92456, 0]
    assert all(r.source == "fastf1" for r in results)


@pytest.mark.unit
def test_map_fastf1_results_rejects_empty_driver() -> None:
    records = [{"Driver": None, "Position": 1, "Time": "1:32.123"}]

    with pytest.raises(ValueError, match="Driver code is required"):
        map_fastf1_results(
            season=2024,
            round_number=1,
            session="R",
            results=records,
            ingested_at="2026-03-13T00:00:00Z",
        )
