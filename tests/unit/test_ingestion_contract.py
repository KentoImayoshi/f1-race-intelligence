import pytest

from f1_ingestion.contracts import RAW_SESSION_RESULTS_COLUMNS, RawSessionResult


@pytest.mark.unit
def test_raw_session_results_contract_columns() -> None:
    assert RAW_SESSION_RESULTS_COLUMNS == [
        "season",
        "round",
        "session",
        "driver_code",
        "position",
        "lap_time_ms",
        "source",
        "ingested_at",
    ]


@pytest.mark.unit
def test_raw_session_result_to_record() -> None:
    record = RawSessionResult(
        season=2024,
        round=1,
        session="R",
        driver_code="VER",
        position=1,
        lap_time_ms=5361234,
        source="seed",
        ingested_at="2026-03-13T00:00:00Z",
    ).to_record()

    assert record["season"] == 2024
    assert record["round"] == 1
    assert record["session"] == "R"
    assert record["driver_code"] == "VER"
    assert record["position"] == 1
    assert record["lap_time_ms"] == 5361234
    assert record["source"] == "seed"
    assert record["ingested_at"] == "2026-03-13T00:00:00Z"
