from __future__ import annotations

import logging

from f1_core.paths import features_dir, insights_dir, llm_dir, models_dir, processed_dir, raw_dir
from f1_core.run_manifest import (
    RunProvenance,
    create_run_manifest,
    infer_execution_status,
    save_run_manifest,
)
from f1_features.features import build_session_analytics, build_session_features
from f1_ingestion.ingestion import (
    ingest_raw_session_laps,
    ingest_raw_session_results,
    ingest_raw_session_telemetry,
)
from f1_insights.insights import build_race_intelligence, build_top_driver_insights
from f1_llm.explanations import (
    build_fallback_explanations,
    build_top_driver_explanations,
)
from f1_models.baseline import build_baseline_driver_scores
from f1_processing.processing import process_session_results

RAW_DIR = raw_dir()
PROCESSED_DIR = processed_dir()
FEATURES_DIR = features_dir()
MODELS_DIR = models_dir()
INSIGHTS_DIR = insights_dir()
LLM_DIR = llm_dir()


BASELINE_MODEL_NAME = "baseline_driver_scores"
BASELINE_MODEL_VERSION = "v1"
EXPLAINER_NAME = "top_driver_explanations"
EXPLAINER_VERSION = "v1"

logger = logging.getLogger(__name__)


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
    raw_laps_path = ingest_raw_session_laps(
        output_dir=RAW_DIR,
        source=source,
        year=year,
        grand_prix=round_value,
        session=session,
    )
    raw_telemetry_path = ingest_raw_session_telemetry(
        output_dir=RAW_DIR,
        source=source,
        year=year,
        grand_prix=round_value,
        session=session,
    )

    processed_path = process_session_results(raw_path=raw_path, output_dir=PROCESSED_DIR)
    features_path = build_session_features(processed_path=processed_path, output_dir=FEATURES_DIR)
    analytics_paths = build_session_analytics(
        laps_path=raw_laps_path,
        telemetry_path=raw_telemetry_path,
        output_dir=FEATURES_DIR,
    )
    model_path = build_baseline_driver_scores(features_path=features_path, output_dir=MODELS_DIR)
    insights_path = build_top_driver_insights(baseline_path=model_path, output_dir=INSIGHTS_DIR)
    intelligence_paths = build_race_intelligence(
        lap_analysis_path=analytics_paths["lap_analysis"],
        sector_performance_path=analytics_paths["sector_performance"],
        tire_stints_path=analytics_paths["tire_stints"],
        driver_consistency_path=analytics_paths["driver_consistency"],
        pace_evolution_path=analytics_paths["pace_evolution"],
        baseline_path=model_path,
        output_dir=INSIGHTS_DIR,
    )
    explanation_status = "ok"
    try:
        explanations_path = build_top_driver_explanations(
            insights_path=insights_path, output_dir=LLM_DIR
        )
    except Exception as exc:  # pragma: no cover - fallback path logging
        explanation_status = "fallback"
        logger.exception("LLM explanation generation failed, writing fallback artifact")
        explanations_path = build_fallback_explanations(output_dir=LLM_DIR, error=exc)

    steps = [
        "ingested raw session results",
        "ingested raw session laps",
        "ingested raw session telemetry",
        "processed raw data",
        "built session features",
        "built telemetry-aware analytics artifacts",
        "computed baseline scores",
        "generated structured insights",
        "generated race intelligence artifacts",
        "created grounded explanations",
    ]

    artifacts = {
        "raw": str(raw_path),
        "raw_laps": str(raw_laps_path),
        "raw_telemetry": str(raw_telemetry_path),
        "processed": str(processed_path),
        "features": str(features_path),
        "lap_analysis": str(analytics_paths["lap_analysis"]),
        "sector_performance": str(analytics_paths["sector_performance"]),
        "tire_stints": str(analytics_paths["tire_stints"]),
        "driver_consistency": str(analytics_paths["driver_consistency"]),
        "pace_evolution": str(analytics_paths["pace_evolution"]),
        "model": str(model_path),
        "insights": str(insights_path),
        "pace_degradation": str(intelligence_paths["pace_degradation"]),
        "sector_dominance": str(intelligence_paths["sector_dominance"]),
        "consistency_scores": str(intelligence_paths["consistency_scores"]),
        "tire_windows": str(intelligence_paths["tire_windows"]),
        "strategy_opportunities": str(intelligence_paths["strategy_opportunities"]),
        "stint_strength": str(intelligence_paths["stint_strength"]),
        "race_pace_rankings": str(intelligence_paths["race_pace_rankings"]),
        "qualifying_race_comparison": str(intelligence_paths["qualifying_race_comparison"]),
        "session_summaries": str(intelligence_paths["session_summaries"]),
        "driver_reports": str(intelligence_paths["driver_reports"]),
        "strategy_summaries": str(intelligence_paths["strategy_summaries"]),
        "race_trends": str(intelligence_paths["race_trends"]),
        "explanations": str(explanations_path),
    }

    execution_status = infer_execution_status(explanation_status)

    provenance = RunProvenance(
        model_name=BASELINE_MODEL_NAME,
        explainer_name=EXPLAINER_NAME,
        model_version=BASELINE_MODEL_VERSION,
        explainer_version=EXPLAINER_VERSION,
    )

    try:
        manifest = create_run_manifest(
            source=source,
            year=year,
            round_value=round_value,
            session=session,
            artifacts=artifacts,
            status="success",
            explanation_status=explanation_status,
            execution_status=execution_status,
            provenance=provenance,
        )
        save_run_manifest(manifest)
    except Exception:  # pragma: no cover - best effort logging
        logger.exception("run manifest persistence failed")

    return {"success": True, "steps": steps, "artifacts": artifacts}
