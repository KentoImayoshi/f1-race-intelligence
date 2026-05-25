from __future__ import annotations

import json

import pyarrow.parquet as pq
import pytest
from f1_ingestion.ingestion import (
    ingest_raw_session_laps,
    ingest_raw_session_results,
    ingest_raw_session_telemetry,
)


@pytest.mark.unit
def test_openf1_results_are_normalized_and_metadata_is_written(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def stub_get_json(url: str, *, params=None, source: str):
        if url.endswith("/sessions"):
            return [
                {
                    "meeting_key": 101,
                    "session_key": 2024,
                    "meeting_name": "Bahrain Grand Prix",
                    "country_name": "Bahrain",
                    "location": "Sakhir",
                    "date_start": "2024-03-02T12:00:00Z",
                }
            ]
        if url.endswith("/drivers"):
            return [
                {"driver_number": 1, "name_acronym": "VER"},
                {"driver_number": 11, "name_acronym": "PER"},
            ]
        if url.endswith("/session_result"):
            return [
                {"driver_number": 1, "position": 1},
                {"driver_number": 11, "position": 2},
            ]
        if url.endswith("/laps"):
            return [
                {"driver_number": 1, "lap_number": 1, "lap_duration": 91.1},
                {"driver_number": 11, "lap_number": 1, "lap_duration": 91.5},
            ]
        raise AssertionError(url)

    monkeypatch.setattr("f1_ingestion.sources._get_json", stub_get_json)

    output_path = ingest_raw_session_results(
        output_dir=tmp_path,
        source="openf1",
        year=2024,
        grand_prix=1,
        session="R",
    )

    rows = pq.read_table(output_path).to_pylist()
    assert [row["driver_code"] for row in rows] == ["VER", "PER"]
    assert [row["position"] for row in rows] == [1, 2]
    assert [row["lap_time_ms"] for row in rows] == [91100, 91500]

    metadata = json.loads(output_path.with_suffix(".parquet.metadata.json").read_text())
    assert metadata["source"] == "openf1"
    assert metadata["resolved_round"] == 1
    assert metadata["resolved_grand_prix"] == "Bahrain Grand Prix"
    assert metadata["result_row_count"] == 2


@pytest.mark.unit
def test_jolpica_results_are_normalized(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    def stub_get_json(url: str, *, params=None, source: str):
        if url.endswith("/2024/1/races/"):
            return {
                "MRData": {
                    "RaceTable": {"Races": [{"round": "1", "raceName": "Bahrain Grand Prix"}]}
                }
            }
        if url.endswith("/2024/1/results/"):
            return {
                "MRData": {
                    "RaceTable": {
                        "Races": [
                            {
                                "Results": [
                                    {
                                        "position": "1",
                                        "Driver": {"code": "VER"},
                                        "FastestLap": {"Time": {"time": "1:31.447"}},
                                    },
                                    {
                                        "position": "2",
                                        "Driver": {"code": "PER"},
                                        "FastestLap": {"Time": {"time": "1:31.700"}},
                                    },
                                ]
                            }
                        ]
                    }
                }
            }
        raise AssertionError(url)

    monkeypatch.setattr("f1_ingestion.sources._get_json", stub_get_json)

    output_path = ingest_raw_session_results(
        output_dir=tmp_path,
        source="jolpica",
        year=2024,
        grand_prix=1,
        session="R",
    )

    rows = pq.read_table(output_path).to_pylist()
    assert [row["driver_code"] for row in rows] == ["VER", "PER"]
    assert [row["position"] for row in rows] == [1, 2]
    assert [row["lap_time_ms"] for row in rows] == [91447, 91700]


@pytest.mark.unit
def test_auto_source_falls_back_to_openf1(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    def stub_load(request, *, fetched_at):
        if request.source == "fastf1":
            raise RuntimeError("FastF1 unavailable")
        return type(
            "Payload",
            (),
            {
                "results": [
                    type(
                        "Record",
                        (),
                        {
                            "to_record": lambda self: {
                                "season": 2024,
                                "round": 1,
                                "session": "R",
                                "driver_code": "VER",
                                "position": 1,
                                "lap_time_ms": 90000,
                                "source": "openf1",
                                "ingested_at": fetched_at,
                            }
                        },
                    )()
                ],
                "metadata": type(
                    "Metadata",
                    (),
                    {
                        "source": "openf1",
                        "resolved_round": 1,
                        "resolved_session": "R",
                        "to_dict": lambda self: {"source": "openf1"},
                    },
                )(),
            },
        )()

    monkeypatch.setattr("f1_ingestion.ingestion.load_session_payload", stub_load)

    output_path = ingest_raw_session_results(
        output_dir=tmp_path,
        source="auto",
        year=2024,
        grand_prix=1,
        session="R",
    )

    rows = pq.read_table(output_path).to_pylist()
    assert len(rows) == 1
    assert rows[0]["source"] == "openf1"


@pytest.mark.unit
def test_openf1_laps_are_normalized(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    def stub_get_json(url: str, *, params=None, source: str):
        if url.endswith("/sessions"):
            return [
                {
                    "meeting_key": 101,
                    "session_key": 2024,
                    "meeting_name": "Bahrain Grand Prix",
                    "country_name": "Bahrain",
                    "location": "Sakhir",
                    "date_start": "2024-03-02T12:00:00Z",
                }
            ]
        if url.endswith("/drivers"):
            return [{"driver_number": 1, "name_acronym": "VER"}]
        if url.endswith("/laps"):
            return [
                {
                    "driver_number": 1,
                    "lap_number": 1,
                    "lap_duration": 91.1,
                    "duration_sector_1": 30.1,
                    "duration_sector_2": 30.2,
                    "duration_sector_3": 30.8,
                    "compound": "SOFT",
                    "stint_number": 1,
                }
            ]
        raise AssertionError(url)

    monkeypatch.setattr("f1_ingestion.sources._get_json", stub_get_json)

    output_path = ingest_raw_session_laps(
        output_dir=tmp_path,
        source="openf1",
        year=2024,
        grand_prix=1,
        session="R",
    )

    rows = pq.read_table(output_path).to_pylist()
    assert len(rows) == 1
    assert rows[0]["driver_code"] == "VER"
    assert rows[0]["lap_time_ms"] == 91100


@pytest.mark.unit
def test_openf1_telemetry_detail_is_normalized(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    def stub_get_json(url: str, *, params=None, source: str):
        if url.endswith("/sessions"):
            return [
                {
                    "meeting_key": 101,
                    "session_key": 2024,
                    "meeting_name": "Bahrain Grand Prix",
                    "country_name": "Bahrain",
                    "location": "Sakhir",
                    "date_start": "2024-03-02T12:00:00Z",
                }
            ]
        if url.endswith("/drivers"):
            return [{"driver_number": 1, "name_acronym": "VER"}]
        if url.endswith("/laps"):
            return [
                {
                    "driver_number": 1,
                    "lap_number": 1,
                    "speed_i1": 205,
                    "speed_i2": 244,
                    "speed_fl": 289,
                    "speed_st": 321,
                    "tyre_age_at_start": 5,
                    "track_status": "1",
                    "is_pit_out_lap": False,
                    "is_pit_in_lap": False,
                }
            ]
        raise AssertionError(url)

    monkeypatch.setattr("f1_ingestion.sources._get_json", stub_get_json)

    output_path = ingest_raw_session_telemetry(
        output_dir=tmp_path,
        source="openf1",
        year=2024,
        grand_prix=1,
        session="R",
    )

    rows = pq.read_table(output_path).to_pylist()
    assert len(rows) == 1
    assert rows[0]["driver_code"] == "VER"
    assert rows[0]["speed_st_kph"] == 321
    assert rows[0]["tyre_life_laps"] == 5
