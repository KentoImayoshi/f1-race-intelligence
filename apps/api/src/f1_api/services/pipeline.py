from __future__ import annotations

from pathlib import Path

from f1_features.features import build_session_features
from f1_ingestion.ingestion import ingest_raw_session_results
from f1_insights.insights import build_top_driver_insights
from f1_llm.explanations import build_top_driver_explanations
from f1_models.baseline import build_baseline_driver_scores
from f1_processing.processing import process_session_results


RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
FEATURES_DIR = Path("data/features")
MODELS_DIR = Path("data/models")
INSIGHTS_DIR = Path("data/insights")
LLM_DIR = Path("data/llm")


def run_session_baseline_pipeline(*, source: str = "seed", year: int | None = None, grand_prix: str | None = None, session: str | None = None) -> dict[str, object]:
    raw_path = ingest_raw_session_results(
        output_dir=RAW_DIR,
        source=source,
        year=year,
        grand_prix=grand_prix,
        session=session,
    )

    processed_path = process_session_results(raw_path=raw_path, output_dir=PROCESSED_DIR)
    features_path = build_session_features(processed_path=processed_path, output_dir=FEATURES_DIR)
    model_path = build_baseline_driver_scores(features_path=features_path, output_dir=MODELS_DIR)
    insights_path = build_top_driver_insights(baseline_path=model_path, output_dir=INSIGHTS_DIR)
    explanations_path = build_top_driver_explanations(insights_path=insights_path, output_dir=LLM_DIR)

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
