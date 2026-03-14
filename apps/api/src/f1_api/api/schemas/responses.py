from __future__ import annotations

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


class PipelineRunArtifacts(BaseModel):
    raw: str
    processed: str
    features: str
    model: str
    insights: str
    explanations: str


class PipelineRunResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the pipeline run succeeded")
    steps: list[str] = Field(..., description="Human-readable description of each completed step")
    artifacts: PipelineRunArtifacts
