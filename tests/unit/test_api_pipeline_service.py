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
        "ingest_raw_session_laps",
        make_stub("ingest_laps", "raw_laps.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "ingest_raw_session_telemetry",
        make_stub("ingest_telemetry", "raw_telemetry.parquet"),
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

    def analytics_stub(*args, **kwargs):
        call_order.append("analytics")
        return {
            "lap_analysis": Path("lap_analysis.parquet"),
            "sector_performance": Path("sector.parquet"),
            "tire_stints": Path("stints.parquet"),
            "driver_consistency": Path("consistency.parquet"),
            "pace_evolution": Path("pace.parquet"),
        }

    monkeypatch.setattr(pipeline_module, "build_session_analytics", analytics_stub)
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

    def intelligence_stub(*args, **kwargs):
        call_order.append("intelligence")
        return {
            "pace_degradation": Path("pace_degradation.parquet"),
            "sector_dominance": Path("sector_dominance.parquet"),
            "consistency_scores": Path("consistency_scores.parquet"),
            "tire_windows": Path("tire_windows.parquet"),
            "strategy_opportunities": Path("strategy_opportunities.parquet"),
            "stint_strength": Path("stint_strength.parquet"),
            "race_pace_rankings": Path("race_pace_rankings.parquet"),
            "qualifying_race_comparison": Path("qualifying_race_comparison.parquet"),
            "session_summaries": Path("session_summaries.parquet"),
            "driver_reports": Path("driver_reports.parquet"),
            "strategy_summaries": Path("strategy_summaries.parquet"),
            "race_trends": Path("race_trends.parquet"),
        }

    monkeypatch.setattr(pipeline_module, "build_race_intelligence", intelligence_stub)
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
        execution_status="success",
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
                "execution_status": execution_status,
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
    assert call_order == [
        "ingest",
        "ingest_laps",
        "ingest_telemetry",
        "process",
        "features",
        "analytics",
        "models",
        "insights",
        "intelligence",
        "explanations",
    ]
    assert result["artifacts"]["raw"] == "raw.parquet"
    assert result["artifacts"]["raw_telemetry"] == "raw_telemetry.parquet"
    assert result["artifacts"]["session_summaries"] == "session_summaries.parquet"
    assert "steps" in result

    assert manifest_calls, "manifest should be created"
    assert manifest_calls[0]["status"] == "success"
    assert manifest_calls[0]["artifacts"]["insights"] == "insights.parquet"
    assert manifest_calls[0]["explanation_status"] == "ok"
    assert saved_manifest == [manifest_object]
    assert manifest_calls[0]["provenance"] is not None
    assert manifest_calls[0]["provenance"].model_name == pipeline_module.BASELINE_MODEL_NAME
    assert manifest_calls[0]["provenance"].explainer_name == pipeline_module.EXPLAINER_NAME
    assert manifest_calls[0]["execution_status"] == "success"


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
        "ingest_raw_session_laps",
        make_stub("ingest_laps", "raw_laps.parquet"),
    )
    monkeypatch.setattr(
        pipeline_module,
        "ingest_raw_session_telemetry",
        make_stub("ingest_telemetry", "raw_telemetry.parquet"),
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

    def analytics_stub(*args, **kwargs):
        call_order.append("analytics")
        return {
            "lap_analysis": Path("lap_analysis.parquet"),
            "sector_performance": Path("sector.parquet"),
            "tire_stints": Path("stints.parquet"),
            "driver_consistency": Path("consistency.parquet"),
            "pace_evolution": Path("pace.parquet"),
        }

    monkeypatch.setattr(pipeline_module, "build_session_analytics", analytics_stub)
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

    def intelligence_stub(*args, **kwargs):
        call_order.append("intelligence")
        return {
            "pace_degradation": Path("pace_degradation.parquet"),
            "sector_dominance": Path("sector_dominance.parquet"),
            "consistency_scores": Path("consistency_scores.parquet"),
            "tire_windows": Path("tire_windows.parquet"),
            "strategy_opportunities": Path("strategy_opportunities.parquet"),
            "stint_strength": Path("stint_strength.parquet"),
            "race_pace_rankings": Path("race_pace_rankings.parquet"),
            "qualifying_race_comparison": Path("qualifying_race_comparison.parquet"),
            "session_summaries": Path("session_summaries.parquet"),
            "driver_reports": Path("driver_reports.parquet"),
            "strategy_summaries": Path("strategy_summaries.parquet"),
            "race_trends": Path("race_trends.parquet"),
        }

    monkeypatch.setattr(pipeline_module, "build_race_intelligence", intelligence_stub)

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
        execution_status="success",
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
                "execution_status": execution_status,
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
    assert manifest_calls[0]["execution_status"] == "degraded"
