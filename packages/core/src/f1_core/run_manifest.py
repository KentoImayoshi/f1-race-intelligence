from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from f1_core.paths import latest_run_manifest_path, run_manifests_dir


class ArtifactAvailability(BaseModel):
    artifact_name: str
    expected_path: str
    exists: bool
    status: str | None = None


class RunProvenance(BaseModel):
    model_name: str
    explainer_name: str
    model_version: str | None = None
    explainer_version: str | None = None


class RunFreshness(BaseModel):
    status: Literal["recent", "stale", "unknown"]
    age_seconds: int


ExecutionStatus = Literal["success", "degraded", "failed"]


FRESHNESS_THRESHOLD_SECONDS = 86_400


class RunManifest(BaseModel):
    run_timestamp: str
    status: str
    source: str
    year: int | None
    round: str | None
    session: str | None
    artifacts: dict[str, str]
    explanation_status: str = "ok"
    provenance: RunProvenance
    execution_status: ExecutionStatus = "success"


def create_run_manifest(
    *,
    source: str,
    year: int | None,
    round_value: str | int | None,
    session: str | None,
    artifacts: dict[str, str],
    status: str = "success",
    explanation_status: str = "ok",
    provenance: RunProvenance,
    execution_status: ExecutionStatus = "success",
) -> RunManifest:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    return RunManifest(
        run_timestamp=now.isoformat().replace("+00:00", "Z"),
        status=status,
        source=source,
        year=year,
        round=_stringify(round_value),
        session=session,
        artifacts=artifacts,
        explanation_status=explanation_status,
        provenance=provenance,
        execution_status=execution_status,
    )


def save_run_manifest(manifest: RunManifest) -> None:
    per_run_name = f"run_manifest_{_sanitize_timestamp(manifest.run_timestamp)}.json"
    per_run = run_manifests_dir() / per_run_name
    per_run.write_text(manifest.model_dump_json(indent=2))
    latest = latest_run_manifest_path()
    latest.write_text(manifest.model_dump_json(indent=2))


def load_latest_run_manifest() -> RunManifest | None:
    latest = latest_run_manifest_path()
    if not latest.exists():
        return None
    return RunManifest.model_validate_json(latest.read_text())


def _sanitize_timestamp(timestamp: str) -> str:
    return "".join(ch for ch in timestamp if ch.isalnum())


def describe_artifact_availability(artifacts: dict[str, str]) -> list[ArtifactAvailability]:
    availability: list[ArtifactAvailability] = []
    for name, artifact_path in artifacts.items():
        path = Path(artifact_path)
        exists = path.exists()
        status = "available" if exists else "missing"
        availability.append(
            ArtifactAvailability(
                artifact_name=name,
                expected_path=str(path),
                exists=exists,
                status=status,
            )
        )
    return availability


def _stringify(value: str | int | None) -> str | None:
    if value is None:
        return None
    return str(value)


def compute_run_freshness(
    run_timestamp: str,
    *,
    now: datetime | None = None,
    threshold_seconds: int = FRESHNESS_THRESHOLD_SECONDS,
) -> RunFreshness:
    if now is None:
        now = datetime.now(timezone.utc)
    try:
        timestamp = datetime.fromisoformat(run_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return RunFreshness(status="unknown", age_seconds=0)
    age_seconds = max(int((now - timestamp).total_seconds()), 0)
    status = "recent" if age_seconds < threshold_seconds else "stale"
    return RunFreshness(status=status, age_seconds=age_seconds)


def describe_run_freshness(manifest: RunManifest) -> RunFreshness:
    return compute_run_freshness(manifest.run_timestamp)


def infer_execution_status(explanation_status: str) -> ExecutionStatus:
    if explanation_status != "ok":
        return "degraded"
    return "success"
