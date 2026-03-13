import pyarrow.parquet as pq
import pytest

from f1_ingestion.contracts import RAW_SESSION_RESULTS_COLUMNS
from f1_ingestion.ingestion import ingest_raw_session_results


@pytest.mark.integration
def test_ingest_writes_parquet(tmp_path) -> None:
    output_path = ingest_raw_session_results(output_dir=tmp_path)

    assert output_path.exists()
    assert output_path.suffix == ".parquet"

    table = pq.read_table(output_path)

    assert table.num_rows == 3
    assert table.schema.names == RAW_SESSION_RESULTS_COLUMNS
