from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel

from f1_core.paths import latest_run_manifest_path, run_manifests_dir


class RunManifest(BaseModel):
    run_timestamp: str
    status: str
    source: str
    year: int | None
    round: str | None
    session: str | None
    artifacts: dict[str, str]


def create_run_manifest(
    *,
    source: str,
    year: int | None,
    round_value: str | int | None,
    session: str | None,
    artifacts: dict[str, str],
    status: str = "success",
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


def _stringify(value: str | int | None) -> str | None:
    if value is None:
        return None
    return str(value)
