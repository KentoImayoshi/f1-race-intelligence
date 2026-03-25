from __future__ import annotations

from f1_core.config import settings
from f1_core.run_manifest import describe_artifact_availability, load_latest_run_manifest
from fastapi import APIRouter, HTTPException
from f1_api.api.schemas.responses import LastRunMetadataResponse

router = APIRouter(prefix=settings.api_v1_prefix)


@router.get("/meta/last-run", response_model=LastRunMetadataResponse)
def last_run_metadata() -> LastRunMetadataResponse:
    manifest = load_latest_run_manifest()
    if manifest is None:
        raise HTTPException(status_code=404, detail="no run manifest available")
    availability = describe_artifact_availability(manifest.artifacts)
    return LastRunMetadataResponse(**manifest.model_dump(), artifact_availability=availability)
