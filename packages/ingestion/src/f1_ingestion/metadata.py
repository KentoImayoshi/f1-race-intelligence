"""Metadata sidecars for ingestion artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


def write_metadata_sidecar(artifact_path: Path, payload: Mapping[str, object]) -> Path:
    sidecar_path = artifact_path.with_suffix(f"{artifact_path.suffix}.metadata.json")
    sidecar_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return sidecar_path
