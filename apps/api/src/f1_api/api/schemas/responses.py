from __future__ import annotations

from f1_core.run_manifest import ArtifactAvailability, RunFreshness, RunManifest
from pydantic import BaseModel, Field


class BaselineDriverScoreRow(BaseModel):
    season: int
    round: int
    session: str
    driver_code: str
    position_numeric: int
    score: float
    model_generated_at: str


class TopDriverInsightRow(BaseModel):
    season: int
    round: int
    session: str
    rank: int
    driver_code: str
    score: float
    insight_generated_at: str


class SessionTopDriverExplanationRow(BaseModel):
    season: int
    round: int
    session: str
    explanation_type: str
    explanation_text: str
    explanation_generated_at: str


class SessionLapAnalysisRow(BaseModel):
    season: int
    round: int
    grand_prix: str
    session: str
    driver_code: str
    lap_number: int
    compound: str | None = None
    stint: int | None = None
    lap_time_ms: int
    lap_time_seconds: float
    sector_1_ms: int | None = None
    sector_2_ms: int | None = None
    sector_3_ms: int | None = None
    delta_to_fastest_ms: int
    delta_to_fastest_pct: float
    lap_rank: int
    top_speed_kph: int | None = None
    tyre_life_laps: int | None = None
    is_personal_best: bool | None = None
    analysis_generated_at: str


class TireStintSummaryRow(BaseModel):
    season: int
    round: int
    grand_prix: str
    session: str
    driver_code: str
    stint: int | None = None
    compound: str | None = None
    lap_count: int
    start_lap: int
    end_lap: int
    avg_lap_time_ms: int
    best_lap_time_ms: int
    avg_delta_to_fastest_ms: int
    avg_top_speed_kph: int | None = None
    analysis_generated_at: str


class PaceEvolutionRow(BaseModel):
    season: int
    round: int
    grand_prix: str
    session: str
    driver_code: str
    lap_number: int
    lap_time_ms: int
    rolling_avg_lap_time_ms: int
    delta_to_fastest_ms: int
    pace_trend: str
    top_speed_kph: int | None = None
    analysis_generated_at: str


class DriverConsistencyRow(BaseModel):
    season: int
    round: int
    grand_prix: str
    session: str
    driver_code: str
    lap_count: int
    avg_lap_time_ms: int
    best_lap_time_ms: int
    lap_time_stddev_ms: int
    consistency_index: float
    avg_delta_to_fastest_ms: int
    top_speed_kph: int | None = None
    analysis_generated_at: str


class PipelineRunArtifacts(BaseModel):
    raw: str
    raw_laps: str | None = None
    raw_telemetry: str | None = None
    processed: str
    features: str
    lap_analysis: str | None = None
    sector_performance: str | None = None
    tire_stints: str | None = None
    driver_consistency: str | None = None
    pace_evolution: str | None = None
    model: str
    insights: str
    explanations: str


class PipelineRunResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the pipeline run succeeded")
    steps: list[str] = Field(..., description="Human-readable description of each completed step")
    artifacts: PipelineRunArtifacts


class LastRunMetadataResponse(RunManifest):
    artifact_availability: list[ArtifactAvailability]
    freshness: RunFreshness
