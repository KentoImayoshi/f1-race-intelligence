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

    result = run_session_baseline_pipeline(source="seed")

    assert result["success"] is True
    assert call_order == ["ingest", "process", "features", "models", "insights", "explanations"]
    assert result["artifacts"]["raw"] == "raw.parquet"
    assert "steps" in result
