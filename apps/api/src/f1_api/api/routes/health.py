from f1_core.paths import (
    data_dir,
    features_dir,
    insights_dir,
    llm_dir,
    models_dir,
    processed_dir,
    raw_dir,
)
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
def root() -> dict:
    return {"service": "f1-api"}


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict:
    """Ensure the local storage layout can be created before traffic is routed."""

    readiness_checks = (
        ("data_dir", data_dir),
        ("raw_dir", raw_dir),
        ("processed_dir", processed_dir),
        ("features_dir", features_dir),
        ("models_dir", models_dir),
        ("insights_dir", insights_dir),
        ("llm_dir", llm_dir),
    )

    directories: dict[str, str] = {}
    try:
        for label, fn in readiness_checks:
            directories[label] = str(fn())
    except OSError as exc:
        raise HTTPException(
            status_code=503,
            detail="unable to prepare data storage directories",
        ) from exc

    return {
        "status": "ready",
        "service": "f1-api",
        "directories": directories,
    }
