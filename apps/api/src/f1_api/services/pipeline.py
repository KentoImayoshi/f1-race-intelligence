from __future__ import annotations

from f1_core.paths import features_dir, insights_dir, llm_dir, models_dir, processed_dir, raw_dir
from f1_features.features import build_session_features
from f1_ingestion.ingestion import ingest_raw_session_results
from f1_insights.insights import build_top_driver_insights
from f1_llm.explanations import build_top_driver_explanations
from f1_models.baseline import build_baseline_driver_scores
from f1_processing.processing import process_session_results

RAW_DIR = raw_dir()
PROCESSED_DIR = processed_dir()
FEATURES_DIR = features_dir()
MODELS_DIR = models_dir()
INSIGHTS_DIR = insights_dir()
LLM_DIR = llm_dir()


def run_session_baseline_pipeline(
    *,
    source: str = "seed",
    year: int | None = None,
    round_value: str | None = None,
    session: str | None = None,
) -> dict[str, object]:
    """The single allowed orchestrator that wires all downstream packages."""
    raw_path = ingest_raw_session_results(
        output_dir=RAW_DIR,
        source=source,
        year=year,
        grand_prix=round_value,
        session=session,
    )

    processed_path = process_session_results(raw_path=raw_path, output_dir=PROCESSED_DIR)
    features_path = build_session_features(processed_path=processed_path, output_dir=FEATURES_DIR)
    model_path = build_baseline_driver_scores(features_path=features_path, output_dir=MODELS_DIR)
    insights_path = build_top_driver_insights(baseline_path=model_path, output_dir=INSIGHTS_DIR)
    explanations_path = build_top_driver_explanations(
        insights_path=insights_path, output_dir=LLM_DIR
    )

    steps = [
        "ingested raw session results",
        "processed raw data",
        "built session features",
        "computed baseline scores",
        "generated structured insights",
        "created grounded explanations",
    ]

    artifacts = {
        "raw": str(raw_path),
        "processed": str(processed_path),
        "features": str(features_path),
        "model": str(model_path),
        "insights": str(insights_path),
        "explanations": str(explanations_path),
    }

    return {"success": True, "steps": steps, "artifacts": artifacts}
