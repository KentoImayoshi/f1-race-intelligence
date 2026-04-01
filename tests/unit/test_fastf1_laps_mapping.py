import pytest
from f1_ingestion.ingestion import map_fastf1_laps


@pytest.mark.unit
def test_map_fastf1_laps_to_raw_contract_with_optional_fields() -> None:
    laps = [
        {
            "Driver": "VER",
            "LapNumber": 1,
            "LapTime": "1:32.123",
            "Sector1Time": "30.123",
            "Sector2Time": "31.000",
            "Sector3Time": "31.000",
            "Compound": "SOFT",
            "Stint": 1,
            "IsPersonalBest": True,
        },
        {
            "Driver": "PER",
            "LapNumber": 2,
            "LapTime": None,
            "Sector1Time": None,
            "Sector2Time": "NaT",
            "Sector3Time": None,
            "Compound": None,
            "Stint": None,
            "IsPersonalBest": None,
        },
    ]

    records = map_fastf1_laps(
        season=2024,
        round_number=1,
        grand_prix="Bahrain Grand Prix",
        session="R",
        laps=laps,
        ingested_at="2026-03-13T00:00:00Z",
    )

    assert len(records) == 2
    assert records[0].driver_code == "VER"
    assert records[0].lap_number == 1
    assert records[0].lap_time_ms == 92123
    assert records[0].sector_1_ms == 30123
    assert records[0].sector_2_ms == 31000
    assert records[0].sector_3_ms == 31000
    assert records[0].compound == "SOFT"
    assert records[0].stint == 1
    assert records[0].is_personal_best is True
    assert records[1].driver_code == "PER"
    assert records[1].lap_number == 2
    assert records[1].lap_time_ms is None
    assert records[1].sector_1_ms is None
    assert records[1].sector_2_ms is None
    assert records[1].sector_3_ms is None
    assert records[1].compound is None
    assert records[1].stint is None
    assert records[1].is_personal_best is None
    assert all(record.source == "fastf1" for record in records)


@pytest.mark.unit
def test_map_fastf1_laps_rejects_missing_lap_number() -> None:
    with pytest.raises(ValueError, match="LapNumber is required"):
        map_fastf1_laps(
            season=2024,
            round_number=1,
            grand_prix="Bahrain Grand Prix",
            session="R",
            laps=[{"Driver": "VER", "LapNumber": None}],
            ingested_at="2026-03-13T00:00:00Z",
        )
