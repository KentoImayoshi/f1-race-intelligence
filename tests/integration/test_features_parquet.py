from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from f1_features.contracts import FEATURE_SESSION_RESULTS_COLUMNS, SESSION_LAP_ANALYSIS_COLUMNS
from f1_features.features import build_session_analytics, build_session_features


@pytest.mark.integration
def test_build_session_features_writes_parquet(tmp_path: Path) -> None:
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
                "processed_at": "2026-03-13T00:00:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "driver_code": "PER",
                "position": 2,
                "lap_time_ms": 0,
                "processed_at": "2026-03-13T00:00:00Z",
            },
        ]
    )
    pq.write_table(table, processed_path)

    output_path = build_session_features(processed_path=processed_path, output_dir=tmp_path)
    out_table = pq.read_table(output_path)

    assert output_path.name == "features_session_results.parquet"
    assert out_table.schema.names == FEATURE_SESSION_RESULTS_COLUMNS
    assert out_table.num_rows == table.num_rows


@pytest.mark.integration
def test_build_session_analytics_writes_parquet_bundle(tmp_path: Path) -> None:
    laps_path = tmp_path / "raw_session_laps.parquet"
    telemetry_path = tmp_path / "raw_session_telemetry.parquet"

    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "VER",
                    "lap_number": 1,
                    "lap_time_ms": 92000,
                    "sector_1_ms": 30100,
                    "sector_2_ms": 30700,
                    "sector_3_ms": 31200,
                    "compound": "SOFT",
                    "stint": 1,
                    "is_personal_best": True,
                    "source": "seed",
                    "ingested_at": "2026-03-13T00:00:00Z",
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "PER",
                    "lap_number": 1,
                    "lap_time_ms": 92500,
                    "sector_1_ms": 30400,
                    "sector_2_ms": 30800,
                    "sector_3_ms": 31300,
                    "compound": "SOFT",
                    "stint": 1,
                    "is_personal_best": True,
                    "source": "seed",
                    "ingested_at": "2026-03-13T00:00:00Z",
                },
            ]
        ),
        laps_path,
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "VER",
                    "lap_number": 1,
                    "speed_i1_kph": 205,
                    "speed_i2_kph": 244,
                    "speed_fl_kph": 288,
                    "speed_st_kph": 321,
                    "tyre_life_laps": 5,
                    "track_status": "1",
                    "is_pit_out_lap": False,
                    "is_pit_in_lap": False,
                    "source": "seed",
                    "ingested_at": "2026-03-13T00:00:00Z",
                },
                {
                    "season": 2024,
                    "round": 1,
                    "grand_prix": "Bahrain Grand Prix",
                    "session": "R",
                    "driver_code": "PER",
                    "lap_number": 1,
                    "speed_i1_kph": 201,
                    "speed_i2_kph": 241,
                    "speed_fl_kph": 286,
                    "speed_st_kph": 318,
                    "tyre_life_laps": 5,
                    "track_status": "1",
                    "is_pit_out_lap": False,
                    "is_pit_in_lap": False,
                    "source": "seed",
                    "ingested_at": "2026-03-13T00:00:00Z",
                },
            ]
        ),
        telemetry_path,
    )

    outputs = build_session_analytics(
        laps_path=laps_path,
        telemetry_path=telemetry_path,
        output_dir=tmp_path,
    )

    lap_analysis_table = pq.read_table(outputs["lap_analysis"])
    assert lap_analysis_table.schema.names == SESSION_LAP_ANALYSIS_COLUMNS
    assert lap_analysis_table.num_rows == 2
    assert pq.read_table(outputs["tire_stints"]).num_rows == 2
