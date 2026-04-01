import pytest
from f1_ingestion.ingestion import ingest_raw_session_laps, ingest_raw_session_results


@pytest.mark.unit
def test_fastf1_requires_parameters(tmp_path) -> None:
    with pytest.raises(ValueError, match="year, grand_prix, and session are required"):
        ingest_raw_session_results(output_dir=tmp_path, source="fastf1")


@pytest.mark.unit
def test_fastf1_import_error_is_actionable(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="FastF1 is not installed"):
        ingest_raw_session_results(
            output_dir=tmp_path,
            source="fastf1",
            year=2024,
            grand_prix=1,
            session="R",
        )


@pytest.mark.unit
def test_fastf1_laps_require_parameters(tmp_path) -> None:
    with pytest.raises(ValueError, match="year, grand_prix, and session are required"):
        ingest_raw_session_laps(output_dir=tmp_path, source="fastf1")


@pytest.mark.unit
def test_lap_ingestion_rejects_non_fastf1_source(tmp_path) -> None:
    with pytest.raises(ValueError, match="supports only the fastf1 source"):
        ingest_raw_session_laps(output_dir=tmp_path, source="seed")
