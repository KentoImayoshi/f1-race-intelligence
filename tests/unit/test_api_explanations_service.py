from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "apps/api/src"))

from f1_api.services.explanations import _filter_rows, load_top_driver_explanations


@pytest.mark.unit
def test_filter_rows_applies_filters():
    rows = [
        {"season": 2024, "round": 1, "session": "R", "rank": 1},
        {"season": 2024, "round": 2, "session": "Q", "rank": 1},
    ]

    filtered = _filter_rows(rows, season=2024, round_number=1, session="R")

    assert filtered == [rows[0]]


@pytest.mark.unit
def test_load_top_driver_explanations_orders_and_limits(tmp_path):
    path = tmp_path / "explanations.parquet"
    table = pa.Table.from_pylist(
        [
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "explanation_generated_at": "2026-03-13T00:01:00Z",
            },
            {
                "season": 2024,
                "round": 1,
                "session": "R",
                "explanation_generated_at": "2026-03-13T00:00:00Z",
            },
        ]
    )
    pq.write_table(table, path)

    rows = load_top_driver_explanations(explanations_path=path, limit=1)

    assert len(rows) == 1
    assert rows[0]["explanation_generated_at"] == "2026-03-13T00:00:00Z"


@pytest.mark.unit
def test_load_top_driver_explanations_limit_validation(tmp_path):
    path = tmp_path / "explanations.parquet"
    pq.write_table(pa.Table.from_pylist([], schema=pa.schema([])), path)

    with pytest.raises(ValueError):
        load_top_driver_explanations(explanations_path=path, limit=0)
