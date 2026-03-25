from pathlib import Path

import pytest
from f1_api.api.routes.meta import last_run_metadata
from f1_api.services import pipeline as pipeline_module
from f1_core import paths
from f1_core.run_manifest import load_latest_run_manifest


@pytest.mark.integration
def test_pipeline_run_updates_last_run_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_root = tmp_path / "data"
    monkeypatch.setattr(paths, "DATA_DIR", data_root)
    pipeline_module.RAW_DIR = paths.raw_dir()
    pipeline_module.PROCESSED_DIR = paths.processed_dir()
    pipeline_module.FEATURES_DIR = paths.features_dir()
    pipeline_module.MODELS_DIR = paths.models_dir()
    pipeline_module.INSIGHTS_DIR = paths.insights_dir()
    pipeline_module.LLM_DIR = paths.llm_dir()

    result = pipeline_module.run_session_baseline_pipeline(
        source="seed",
        round_value="1",
        session="R",
    )
    assert result["success"] is True

    manifest = load_latest_run_manifest()
    assert manifest is not None
    assert manifest.status == "success"
    assert manifest.round == "1"
    assert manifest.session == "R"
    assert "raw" in manifest.artifacts

    response = last_run_metadata()
    assert response.run_timestamp == manifest.run_timestamp
    assert response.artifacts == manifest.artifacts
    assert response.artifact_availability
    assert any(
        entry.artifact_name == "raw" and entry.exists for entry in response.artifact_availability
    )
    assert response.provenance.model_name == pipeline_module.BASELINE_MODEL_NAME
    assert response.provenance.explainer_name == pipeline_module.EXPLAINER_NAME
    assert response.freshness.status in {"recent", "stale", "unknown"}
