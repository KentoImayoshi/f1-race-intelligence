import pytest
from fastapi import HTTPException

from f1_api.api.routes.meta import last_run_metadata
from f1_core.run_manifest import RunManifest


@pytest.mark.unit
def test_last_run_metadata_returns_manifest(monkeypatch) -> None:
    sample_manifest = RunManifest(
        run_timestamp="2024-01-01T00:00:00Z",
        status="success",
        source="seed",
        year=2024,
        round="1",
        session="R",
        artifacts={},
    )

    monkeypatch.setattr("f1_api.api.routes.meta.load_latest_run_manifest", lambda: sample_manifest)

    assert last_run_metadata() == sample_manifest


@pytest.mark.unit
def test_last_run_metadata_missing(monkeypatch) -> None:
    monkeypatch.setattr("f1_api.api.routes.meta.load_latest_run_manifest", lambda: None)

    with pytest.raises(HTTPException) as excinfo:
        last_run_metadata()

    assert excinfo.value.status_code == 404
