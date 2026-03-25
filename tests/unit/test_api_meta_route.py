import pytest
from f1_api.api.routes.meta import last_run_metadata
from f1_core.run_manifest import (
    ArtifactAvailability,
    RunFreshness,
    RunManifest,
    RunProvenance,
)
from fastapi import HTTPException


@pytest.mark.unit
def test_last_run_metadata_returns_manifest(monkeypatch) -> None:
    provenance = RunProvenance(model_name="baseline", explainer_name="explain")
    sample_manifest = RunManifest(
        run_timestamp="2024-01-01T00:00:00Z",
        status="success",
        source="seed",
        year=2024,
        round="1",
        session="R",
        artifacts={},
        provenance=provenance,
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

    monkeypatch.setattr(
        "f1_api.api.routes.meta.describe_run_freshness",
        lambda manifest: RunFreshness(status="recent", age_seconds=5),
    )

    response = last_run_metadata()

    assert response.artifact_availability == availability
    assert response.run_timestamp == sample_manifest.run_timestamp
    assert response.artifacts == sample_manifest.artifacts
    assert response.provenance == sample_manifest.provenance
    assert response.freshness.status == "recent"
    assert response.execution_status == "success"


@pytest.mark.unit
def test_last_run_metadata_missing(monkeypatch) -> None:
    monkeypatch.setattr("f1_api.api.routes.meta.load_latest_run_manifest", lambda: None)

    with pytest.raises(HTTPException) as excinfo:
        last_run_metadata()

    assert excinfo.value.status_code == 404


@pytest.mark.contract
def test_last_run_metadata_contract(monkeypatch) -> None:
    provenance = RunProvenance(
        model_name="baseline_driver_scores",
        explainer_name="top_driver_explanations",
        model_version="v1",
        explainer_version="v1",
    )
    manifest = RunManifest(
        run_timestamp="2024-02-01T00:00:00Z",
        status="success",
        source="seed",
        year=2024,
        round="2",
        session="Q",
        artifacts={"raw": "data/raw.parquet"},
        provenance=provenance,
    )

    availability = [
        ArtifactAvailability(
            artifact_name="raw",
            expected_path="data/raw.parquet",
            exists=True,
            status="available",
        )
    ]

    monkeypatch.setattr(
        "f1_api.api.routes.meta.load_latest_run_manifest",
        lambda: manifest,
    )
    monkeypatch.setattr(
        "f1_api.api.routes.meta.describe_artifact_availability",
        lambda artifacts: availability,
    )
    monkeypatch.setattr(
        "f1_api.api.routes.meta.describe_run_freshness",
        lambda manifest: RunFreshness(status="recent", age_seconds=10),
    )

    response = last_run_metadata()
    payload = response.model_dump()

    assert payload["status"] == "success"
    assert payload["year"] == 2024
    assert payload["round"] == "2"
    assert payload["artifacts"]["raw"] == "data/raw.parquet"
    assert isinstance(payload["artifact_availability"], list)
    assert payload["artifact_availability"][0]["artifact_name"] == "raw"
    assert payload["artifact_availability"][0]["status"] == "available"
    assert payload["provenance"]["model_name"] == "baseline_driver_scores"
    assert payload["provenance"]["model_version"] == "v1"
    assert payload["provenance"]["explainer_name"] == "top_driver_explanations"
    assert payload["provenance"]["explainer_version"] == "v1"
    assert payload["freshness"]["status"] == "recent"
    assert payload["freshness"]["age_seconds"] == 10
    assert payload["execution_status"] == "success"
