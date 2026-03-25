from pathlib import Path

import pytest
from f1_core import paths
from f1_core.run_manifest import (
    create_run_manifest,
    describe_artifact_availability,
    load_latest_run_manifest,
    run_manifests_dir,
    save_run_manifest,
)


@pytest.mark.unit
def test_run_manifest_persists_and_loads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact_dir = tmp_path / "data"
    monkeypatch.setattr(paths, "DATA_DIR", artifact_dir)

    manifest = create_run_manifest(
        source="seed",
        year=2025,
        round_value="3",
        session="R",
        artifacts={"raw": "raw.parquet"},
    )

    save_run_manifest(manifest)

    latest = load_latest_run_manifest()

    assert latest is not None
    assert latest.run_timestamp == manifest.run_timestamp
    assert latest.status == manifest.status
    assert latest.round == "3"

    stored = list(run_manifests_dir().glob("run_manifest_*.json"))
    assert stored, "per-run manifest should exist"


@pytest.mark.unit
def test_describe_artifact_availability_detects_missing_files(tmp_path: Path) -> None:
    present = tmp_path / "present.parquet"
    present.write_text("data")
    artifacts = {
        "present": str(present),
        "missing": str(tmp_path / "missing.parquet"),
    }

    availability = describe_artifact_availability(artifacts)

    names = {entry.artifact_name for entry in availability}
    assert names == {"present", "missing"}

    present_entry = next(entry for entry in availability if entry.artifact_name == "present")
    missing_entry = next(entry for entry in availability if entry.artifact_name == "missing")

    assert present_entry.exists
    assert present_entry.status == "available"
    assert missing_entry.exists is False
    assert missing_entry.status == "missing"
