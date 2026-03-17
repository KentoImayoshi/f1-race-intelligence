from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest


from f1_api.services.insights import _filter_rows, load_top_driver_insights


@pytest.mark.unit
def test_filter_rows_applies_all_filters():
    rows = [
        {"season": 2024, "round": 1, "session": "R", "rank": 1},
        {"season": 2024, "round": 2, "session": "R", "rank": 2},
    ]

    filtered = _filter_rows(rows, season=2024, round_number=1, session="R")

    assert filtered == [rows[0]]


@pytest.mark.unit
def test_load_top_driver_insights_orders_and_limits(tmp_path):
    path = tmp_path / "insights.parquet"
    table = pa.Table.from_pylist(
        [
            {"season": 2024, "round": 1, "session": "R", "rank": 2},
            {"season": 2024, "round": 1, "session": "R", "rank": 1},
        ]
    )
    pq.write_table(table, path)

    rows = load_top_driver_insights(insights_path=path, limit=1)

    assert len(rows) == 1
    assert rows[0]["rank"] == 1


@pytest.mark.unit
def test_load_top_driver_insights_limit_validation(tmp_path):
    path = tmp_path / "insights.parquet"
    pq.write_table(pa.Table.from_pylist([], schema=pa.schema([])), path)

    with pytest.raises(ValueError):
        load_top_driver_insights(insights_path=path, limit=0)
