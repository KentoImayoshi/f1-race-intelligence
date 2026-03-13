import os
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from f1_ingestion.contracts import RAW_SESSION_RESULTS_COLUMNS
from f1_ingestion.ingestion import ingest_raw_session_results


@pytest.mark.integration
def test_fastf1_real_ingestion(tmp_path: Path) -> None:
    if os.getenv("RUN_FASTF1_INTEGRATION") != "1":
        pytest.skip("Set RUN_FASTF1_INTEGRATION=1 to run real FastF1 ingestion.")

    output_path = ingest_raw_session_results(
        output_dir=tmp_path,
        source="fastf1",
        year=2024,
        grand_prix=1,
        session="R",
    )

    table = pq.read_table(output_path)

    assert output_path.name == "raw_session_results.parquet"
    assert table.schema.names == RAW_SESSION_RESULTS_COLUMNS
    assert table.num_rows > 0
