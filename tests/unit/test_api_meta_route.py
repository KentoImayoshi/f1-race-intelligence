import pytest
from f1_api.api.routes.meta import last_run_metadata
from f1_core.run_manifest import ArtifactAvailability, RunManifest
from fastapi import HTTPException


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

    availability = [
        ArtifactAvailability(
            artifact_name="raw",
            expected_path="raw.parquet",
            exists=True,
            status="available",
        )
    ]

    monkeypatch.setattr(
        "f1_api.api.routes.meta.load_latest_run_manifest",
        lambda: sample_manifest,
    )
    monkeypatch.setattr(
        "f1_api.api.routes.meta.describe_artifact_availability",
        lambda artifacts: availability,
    )

    response = last_run_metadata()

    assert response.artifact_availability == availability
    assert response.run_timestamp == sample_manifest.run_timestamp
    assert response.artifacts == sample_manifest.artifacts


@pytest.mark.unit
def test_last_run_metadata_missing(monkeypatch) -> None:
    monkeypatch.setattr("f1_api.api.routes.meta.load_latest_run_manifest", lambda: None)

    with pytest.raises(HTTPException) as excinfo:
        last_run_metadata()

    assert excinfo.value.status_code == 404
