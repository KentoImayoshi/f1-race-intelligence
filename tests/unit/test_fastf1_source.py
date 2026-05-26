import pytest
from f1_ingestion import sources
from f1_ingestion.ingestion import (
    ingest_raw_session_laps,
    ingest_raw_session_results,
    ingest_raw_session_telemetry,
)


@pytest.mark.unit
def test_fastf1_requires_parameters(tmp_path) -> None:
    with pytest.raises(ValueError, match="year, grand_prix, and session are required"):
        ingest_raw_session_results(output_dir=tmp_path, source="fastf1")


@pytest.mark.unit
def test_fastf1_import_error_is_actionable(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import builtins

    original_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "fastf1":
            raise ModuleNotFoundError("No module named 'fastf1'")
        return original_import(name, *args, **kwargs)

    monkeypatch.delitem(sources.__dict__, "fastf1", raising=False)
    monkeypatch.setattr(builtins, "__import__", _fake_import)

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
def test_fastf1_telemetry_requires_parameters(tmp_path) -> None:
    with pytest.raises(ValueError, match="year, grand_prix, and session are required"):
        ingest_raw_session_telemetry(output_dir=tmp_path, source="fastf1")
