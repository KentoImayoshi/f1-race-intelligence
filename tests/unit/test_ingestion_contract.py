import pytest
from f1_ingestion.contracts import (
    RAW_SESSION_LAPS_COLUMNS,
    RAW_SESSION_RESULTS_COLUMNS,
    RawSessionLap,
    RawSessionResult,
)


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


@pytest.mark.unit
def test_raw_session_laps_contract_columns() -> None:
    assert RAW_SESSION_LAPS_COLUMNS == [
        "season",
        "round",
        "grand_prix",
        "session",
        "driver_code",
        "lap_number",
        "lap_time_ms",
        "sector_1_ms",
        "sector_2_ms",
        "sector_3_ms",
        "compound",
        "stint",
        "is_personal_best",
        "source",
        "ingested_at",
    ]


@pytest.mark.unit
def test_raw_session_lap_to_record() -> None:
    record = RawSessionLap(
        season=2024,
        round=1,
        grand_prix="Bahrain Grand Prix",
        session="R",
        driver_code="VER",
        lap_number=12,
        lap_time_ms=92123,
        sector_1_ms=30123,
        sector_2_ms=30999,
        sector_3_ms=31001,
        compound="SOFT",
        stint=1,
        is_personal_best=True,
        source="fastf1",
        ingested_at="2026-03-13T00:00:00Z",
    ).to_record()

    assert record["season"] == 2024
    assert record["round"] == 1
    assert record["grand_prix"] == "Bahrain Grand Prix"
    assert record["session"] == "R"
    assert record["driver_code"] == "VER"
    assert record["lap_number"] == 12
    assert record["lap_time_ms"] == 92123
    assert record["sector_1_ms"] == 30123
    assert record["sector_2_ms"] == 30999
    assert record["sector_3_ms"] == 31001
    assert record["compound"] == "SOFT"
    assert record["stint"] == 1
    assert record["is_personal_best"] is True
    assert record["source"] == "fastf1"
    assert record["ingested_at"] == "2026-03-13T00:00:00Z"
