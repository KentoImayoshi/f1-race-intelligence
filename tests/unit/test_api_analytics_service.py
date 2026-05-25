import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from f1_api.services.analytics import (
    _filter_rows,
    load_driver_lap_comparison,
    load_session_lap_analysis,
)


@pytest.mark.unit
def test_filter_rows_applies_driver_filter() -> None:
    rows = [
        {"season": 2024, "round": 1, "session": "R", "driver_code": "VER"},
        {"season": 2024, "round": 1, "session": "R", "driver_code": "PER"},
    ]

    filtered = _filter_rows(
        rows,
        season=2024,
        round_number=1,
        session="R",
        driver_code="VER",
    )

    assert filtered == [rows[0]]


@pytest.mark.unit
def test_load_session_lap_analysis_orders_by_driver_and_lap(tmp_path) -> None:
    path = tmp_path / "lap_analysis.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"season": 2024, "round": 1, "session": "R", "driver_code": "VER", "lap_number": 2},
                {"season": 2024, "round": 1, "session": "R", "driver_code": "VER", "lap_number": 1},
            ]
        ),
        path,
    )

    rows = load_session_lap_analysis(artifact_path=path, limit=10)

    assert [row["lap_number"] for row in rows] == [1, 2]


@pytest.mark.unit
def test_load_driver_lap_comparison_limits_to_requested_pair(tmp_path) -> None:
    path = tmp_path / "lap_analysis.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {"season": 2024, "round": 1, "session": "R", "driver_code": "VER", "lap_number": 1},
                {"season": 2024, "round": 1, "session": "R", "driver_code": "PER", "lap_number": 1},
                {"season": 2024, "round": 1, "session": "R", "driver_code": "LEC", "lap_number": 1},
            ]
        ),
        path,
    )

    rows = load_driver_lap_comparison(
        artifact_path=path,
        season=2024,
        round_number=1,
        session="R",
        driver_code="VER",
        compare_driver="PER",
        limit=10,
    )

    assert {row["driver_code"] for row in rows} == {"VER", "PER"}
