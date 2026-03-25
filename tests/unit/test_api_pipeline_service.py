from pathlib import Path

import pytest
from f1_api.services import pipeline as pipeline_module
from f1_api.services.pipeline import run_session_baseline_pipeline


@pytest.mark.unit
def test_run_session_baseline_pipeline(monkeypatch):
    call_order = []

    def make_stub(name: str, path_suffix: str):
        def stub(*args, **kwargs):
            call_order.append(name)
            return Path(path_suffix)

        return stub

    monkeypatch.setattr(
        pipeline_module,
        "ingest_raw_session_results",
        make_stub("ingest", "raw.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "process_session_results",
        make_stub("process", "processed.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "build_session_features",
        make_stub("features", "features.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "build_baseline_driver_scores",
        make_stub("models", "models.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "build_top_driver_insights",
        make_stub("insights", "insights.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "build_top_driver_explanations",
        make_stub("explanations", "explanations.parquet"),
    )

    manifest_object = object()
    manifest_calls: list[dict[str, object]] = []

    def stub_create_run_manifest(
        *,
        source,
        year,
        round_value,
        session,
        artifacts,
        status,
        explanation_status="ok",
        provenance=None,
    ):
        manifest_calls.append(
            {
                "source": source,
                "year": year,
                "round_value": round_value,
                "session": session,
                "artifacts": artifacts,
                "status": status,
                "explanation_status": explanation_status,
                "provenance": provenance,
            }
        )
        return manifest_object

    saved_manifest: list[object] = []

    def stub_save_run_manifest(manifest):
        saved_manifest.append(manifest)

    monkeypatch.setattr(pipeline_module, "create_run_manifest", stub_create_run_manifest)
    monkeypatch.setattr(pipeline_module, "save_run_manifest", stub_save_run_manifest)

    result = run_session_baseline_pipeline(source="seed")

    assert result["success"] is True
    assert call_order == ["ingest", "process", "features", "models", "insights", "explanations"]
    assert result["artifacts"]["raw"] == "raw.parquet"
    assert "steps" in result

    assert manifest_calls, "manifest should be created"
    assert manifest_calls[0]["status"] == "success"
    assert manifest_calls[0]["artifacts"]["insights"] == "insights.parquet"
    assert manifest_calls[0]["explanation_status"] == "ok"
    assert saved_manifest == [manifest_object]
    assert manifest_calls[0]["provenance"] is not None
    assert manifest_calls[0]["provenance"].model_name == pipeline_module.BASELINE_MODEL_NAME
    assert manifest_calls[0]["provenance"].explainer_name == pipeline_module.EXPLAINER_NAME


@pytest.mark.unit
def test_pipeline_explanation_failure_triggers_fallback(monkeypatch):
    call_order = []

    def make_stub(name: str, path_suffix: str):
        def stub(*args, **kwargs):
            call_order.append(name)
            return Path(path_suffix)

        return stub

    monkeypatch.setattr(
        pipeline_module,
        "ingest_raw_session_results",
        make_stub("ingest", "raw.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "process_session_results",
        make_stub("process", "processed.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "build_session_features",
        make_stub("features", "features.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "build_baseline_driver_scores",
        make_stub("models", "models.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "build_top_driver_insights",
        make_stub("insights", "insights.parquet"),
    )

    def failing_explanations(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(
        pipeline_module,
        "build_top_driver_explanations",
        failing_explanations,
    )

    fallback_path = Path("fallback.parquet")
    fallback_errors: list[Exception] = []

    def stub_fallback_explanations(*, output_dir, error):
        fallback_errors.append(error)
        return fallback_path

    monkeypatch.setattr(
        pipeline_module,
        "build_fallback_explanations",
        stub_fallback_explanations,
    )

    manifest_object = object()
    manifest_calls: list[dict[str, object]] = []

    def stub_create_run_manifest(
        *,
        source,
        year,
        round_value,
        session,
        artifacts,
        status,
        explanation_status="ok",
        provenance=None,
    ):
        manifest_calls.append(
            {
                "source": source,
                "year": year,
                "round_value": round_value,
                "session": session,
                "artifacts": artifacts,
                "status": status,
                "explanation_status": explanation_status,
                "provenance": provenance,
            }
        )
        return manifest_object

    saved_manifest: list[object] = []

    def stub_save_run_manifest(manifest):
        saved_manifest.append(manifest)

    monkeypatch.setattr(pipeline_module, "create_run_manifest", stub_create_run_manifest)
    monkeypatch.setattr(pipeline_module, "save_run_manifest", stub_save_run_manifest)

    result = run_session_baseline_pipeline(source="seed")

    assert result["success"] is True
    assert result["artifacts"]["explanations"] == str(fallback_path)
    assert fallback_errors, "fallback should be invoked"
    assert manifest_calls[0]["explanation_status"] == "fallback"
    assert manifest_calls[0]["provenance"] is not None
