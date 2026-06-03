from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from f1_features.features import build_session_analytics, build_session_features


@pytest.mark.unit
def test_features_require_processed_columns(tmp_path: Path) -> None:
    processed_path = tmp_path / "processed_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position": 1,
                "lap_time_ms": 92123,
            }
        ]
    )
    pq.write_table(table, processed_path)

    with pytest.raises(ValueError, match="Missing required processed columns: processed_at"):
        build_session_features(processed_path=processed_path, output_dir=tmp_path)


@pytest.mark.unit
def test_position_numeric_requires_valid_position(tmp_path: Path) -> None:
    processed_path = tmp_path / "processed_session_results.parquet"

    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "VER",
                "position": None,
                "lap_time_ms": 92123,
                "processed_at": "2026-03-13T00:00:00Z",
            }
        ]
    )
    pq.write_table(table, processed_path)

    with pytest.raises(ValueError, match=r"Invalid position value \(row 0\)"):
        build_session_features(processed_path=processed_path, output_dir=tmp_path)


@pytest.mark.unit
def test_session_analytics_drops_rows_without_driver_code(tmp_path: Path) -> None:
    laps_path = tmp_path / "raw_session_laps.parquet"
    telemetry_path = tmp_path / "raw_session_telemetry.parquet"

    lap_rows = [
        {
            "season": 2024,
            "round": 1,
            "grand_prix": "Bahrain Grand Prix",
            "session": "R",
            "driver_code": None,
            "lap_number": 1,
            "lap_time_ms": 92000,
            "sector_1_ms": 30100,
            "sector_2_ms": 30700,
            "sector_3_ms": 31200,
            "compound": "SOFT",
            "stint": 1,
            "is_personal_best": True,
            "source": "fastf1",
            "ingested_at": "2026-03-13T00:00:00Z",
        },
        {
            "season": 2024,
            "round": 1,
            "grand_prix": "Bahrain Grand Prix",
            "session": "R",
            "driver_code": "ver",
            "lap_number": 1,
            "lap_time_ms": 91800,
            "sector_1_ms": 30000,
            "sector_2_ms": 30600,
            "sector_3_ms": 31200,
            "compound": "SOFT",
            "stint": 1,
            "is_personal_best": True,
            "source": "fastf1",
            "ingested_at": "2026-03-13T00:00:00Z",
        },
    ]
    telemetry_rows = [
        {
            "season": 2024,
            "round": 1,
            "grand_prix": "Bahrain Grand Prix",
            "session": "R",
            "driver_code": "ver",
            "lap_number": 1,
            "speed_i1_kph": 205,
            "speed_i2_kph": 244,
            "speed_fl_kph": 288,
            "speed_st_kph": 321,
            "tyre_life_laps": 5,
            "track_status": "1",
            "is_pit_out_lap": False,
            "is_pit_in_lap": False,
            "source": "fastf1",
            "ingested_at": "2026-03-13T00:00:00Z",
        }
    ]
    pq.write_table(pa.Table.from_pylist(lap_rows), laps_path)
    pq.write_table(pa.Table.from_pylist(telemetry_rows), telemetry_path)

    outputs = build_session_analytics(
        laps_path=laps_path,
        telemetry_path=telemetry_path,
        output_dir=tmp_path,
    )

    rows = pq.read_table(outputs["lap_analysis"]).to_pylist()
    assert [row["driver_code"] for row in rows] == ["VER"]
