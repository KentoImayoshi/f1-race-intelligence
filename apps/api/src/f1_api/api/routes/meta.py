from __future__ import annotations

from fastapi import APIRouter, HTTPException

from f1_core.config import settings
from f1_core.run_manifest import RunManifest, load_latest_run_manifest

router = APIRouter(prefix=settings.api_v1_prefix)


@router.get("/meta/last-run", response_model=RunManifest)
def last_run_metadata() -> RunManifest:
    manifest = load_latest_run_manifest()
    if manifest is None:
        raise HTTPException(status_code=404, detail="no run manifest available")
    return manifest
