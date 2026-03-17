from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from f1_api.services.models import _filter_rows, load_baseline_driver_scores


@pytest.mark.unit
def test_filter_rows_selects_session():
    rows = [
        {"season": 2024, "round": 1, "session": "R"},
        {"season": 2024, "round": 2, "session": "Q"},
    ]

    filtered = _filter_rows(rows, season=2024, round_number=1, session="R")

    assert filtered == [rows[0]]


@pytest.mark.unit
def test_load_baseline_driver_scores_orders(tmp_path):
    path = tmp_path / "models.parquet"
    table = pa.Table.from_pylist(
        [
            {"season": 2024, "round": 1, "session": "R", "driver_code": "PER"},
            {"season": 2024, "round": 1, "session": "R", "driver_code": "VER"},
        ]
    )
    pq.write_table(table, path)

    rows = load_baseline_driver_scores(models_path=path, limit=1)

    assert len(rows) == 1
    assert rows[0]["driver_code"] == "PER"


@pytest.mark.unit
def test_load_baseline_driver_scores_limit_validation(tmp_path):
    path = tmp_path / "models.parquet"
    pq.write_table(pa.Table.from_pylist([], schema=pa.schema([])), path)

    with pytest.raises(ValueError):
        load_baseline_driver_scores(models_path=path, limit=0)
