import pytest

from f1_ingestion.ingestion import ingest_raw_session_results


@pytest.mark.unit
def test_seed_source_returns_parquet(tmp_path) -> None:
    output_path = ingest_raw_session_results(output_dir=tmp_path, source="seed")

    assert output_path.name == "raw_session_results.parquet"


@pytest.mark.unit
def test_fastf1_source_requires_parameters(tmp_path) -> None:
    with pytest.raises(ValueError, match="year, grand_prix, and session are required"):
        ingest_raw_session_results(output_dir=tmp_path, source="fastf1")
