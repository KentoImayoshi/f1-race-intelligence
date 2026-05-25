import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from f1_api.services.intelligence import (
    _filter_rows,
    load_driver_intelligence_reports,
    load_session_intelligence_summaries,
)


@pytest.mark.unit
def test_intelligence_filter_rows_applies_driver_filter() -> None:
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
def test_load_session_intelligence_summaries_orders_by_importance(tmp_path) -> None:
    path = tmp_path / "session_summaries.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "season": 2024,
                    "round": 1,
                    "session": "R",
                    "importance_score": 70.0,
                    "headline": "B",
                },
                {
                    "season": 2024,
                    "round": 1,
                    "session": "R",
                    "importance_score": 90.0,
                    "headline": "A",
                },
            ]
        ),
        path,
    )

    rows = load_session_intelligence_summaries(artifact_path=path, limit=1)

    assert len(rows) == 1
    assert rows[0]["headline"] == "A"


@pytest.mark.unit
def test_load_driver_intelligence_reports_limit_validation(tmp_path) -> None:
    path = tmp_path / "driver_reports.parquet"
    pq.write_table(pa.Table.from_pylist([], schema=pa.schema([])), path)

    with pytest.raises(ValueError):
        load_driver_intelligence_reports(artifact_path=path, limit=0)
