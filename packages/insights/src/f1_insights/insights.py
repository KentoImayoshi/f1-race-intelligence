"""Structured insights and deterministic race intelligence artifacts."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from f1_insights.contracts import (
    INSIGHT_SESSION_TOP_DRIVERS_COLUMNS,
    INTELLIGENCE_CONSISTENCY_SCORES_COLUMNS,
    INTELLIGENCE_DRIVER_REPORT_COLUMNS,
    INTELLIGENCE_PACE_DEGRADATION_COLUMNS,
    INTELLIGENCE_QUALIFYING_RACE_COMPARISON_COLUMNS,
    INTELLIGENCE_RACE_PACE_RANKINGS_COLUMNS,
    INTELLIGENCE_RACE_TREND_COLUMNS,
    INTELLIGENCE_SECTOR_DOMINANCE_COLUMNS,
    INTELLIGENCE_SESSION_SUMMARY_COLUMNS,
    INTELLIGENCE_STINT_STRENGTH_COLUMNS,
    INTELLIGENCE_STRATEGY_OPPORTUNITIES_COLUMNS,
    INTELLIGENCE_STRATEGY_SUMMARY_COLUMNS,
    INTELLIGENCE_TIRE_WINDOWS_COLUMNS,
)

REQUIRED_BASELINE_COLUMNS = {
    "season",
    "round",
    "session",
    "driver_code",
    "score",
    "position_numeric",
    "model_generated_at",
}

REQUIRED_LAP_ANALYSIS_COLUMNS = {
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "compound",
    "stint",
    "lap_time_ms",
    "delta_to_fastest_ms",
    "lap_rank",
    "top_speed_kph",
}

REQUIRED_SECTOR_COLUMNS = {
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "sector_1_delta_ms",
    "sector_2_delta_ms",
    "sector_3_delta_ms",
}

REQUIRED_TIRE_STINT_COLUMNS = {
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "stint",
    "compound",
    "lap_count",
    "avg_lap_time_ms",
    "best_lap_time_ms",
    "avg_delta_to_fastest_ms",
    "avg_top_speed_kph",
}

REQUIRED_CONSISTENCY_COLUMNS = {
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_count",
    "avg_lap_time_ms",
    "best_lap_time_ms",
    "lap_time_stddev_ms",
    "consistency_index",
    "avg_delta_to_fastest_ms",
    "top_speed_kph",
}

REQUIRED_PACE_COLUMNS = {
    "season",
    "round",
    "grand_prix",
    "session",
    "driver_code",
    "lap_number",
    "lap_time_ms",
    "rolling_avg_lap_time_ms",
    "delta_to_fastest_ms",
    "pace_trend",
}

logger = logging.getLogger(__name__)


def build_top_driver_insights(*, baseline_path: Path, output_dir: Path, top_n: int = 3) -> Path:
    """Build top driver insights per session from baseline scores."""
    if top_n <= 0:
        raise ValueError("top_n must be greater than 0")

    table = pq.read_table(baseline_path)
    missing = REQUIRED_BASELINE_COLUMNS.difference(table.schema.names)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required baseline columns: {missing_list}")

    insight_generated_at = _timestamp_now()
    rows = _valid_rows_with_driver_codes(table.to_pylist(), label="baseline")
    grouped: dict[tuple[int, int, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[_session_key(row)].append(row)

    records = []
    for (season, round_number, session), group_rows in grouped.items():
        sorted_rows = sorted(group_rows, key=lambda r: (-float(r["score"]), str(r["driver_code"])))
        for rank, row in enumerate(sorted_rows[:top_n], start=1):
            records.append(
                {
                    "season": season,
                    "round": round_number,
                    "session": session,
                    "rank": rank,
                    "driver_code": row["driver_code"],
                    "score": float(row["score"]),
                    "insight_generated_at": insight_generated_at,
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "insights_session_top_drivers.parquet"
    pq.write_table(pa.Table.from_pylist(records, schema=_top_driver_schema()), output_path)
    return output_path


def build_race_intelligence(
    *,
    lap_analysis_path: Path,
    sector_performance_path: Path,
    tire_stints_path: Path,
    driver_consistency_path: Path,
    pace_evolution_path: Path,
    baseline_path: Path,
    output_dir: Path,
) -> dict[str, Path]:
    """Build deterministic race-intelligence artifacts on top of analytics parquet tables."""
    lap_rows = _read_rows(lap_analysis_path, REQUIRED_LAP_ANALYSIS_COLUMNS, "lap analysis")
    sector_rows = _read_rows(sector_performance_path, REQUIRED_SECTOR_COLUMNS, "sector performance")
    tire_rows = _read_rows(tire_stints_path, REQUIRED_TIRE_STINT_COLUMNS, "tire stints")
    consistency_rows = _read_rows(
        driver_consistency_path, REQUIRED_CONSISTENCY_COLUMNS, "driver consistency"
    )
    pace_rows = _read_rows(pace_evolution_path, REQUIRED_PACE_COLUMNS, "pace evolution")
    baseline_rows = _read_rows(baseline_path, REQUIRED_BASELINE_COLUMNS, "baseline")

    generated_at = _timestamp_now()
    pace_degradation = _build_pace_degradation_rows(pace_rows, generated_at)
    sector_dominance = _build_sector_dominance_rows(sector_rows, generated_at)
    consistency_scores = _build_consistency_score_rows(consistency_rows, generated_at)
    tire_windows = _build_tire_window_rows(lap_rows, generated_at)
    strategy_opportunities = _build_strategy_opportunity_rows(
        tire_rows=tire_rows,
        pace_rows=pace_rows,
        generated_at=generated_at,
    )
    stint_strength = _build_stint_strength_rows(tire_rows, generated_at)
    race_pace_rankings = _build_race_pace_ranking_rows(
        consistency_rows=consistency_rows,
        baseline_rows=baseline_rows,
        generated_at=generated_at,
    )
    qualifying_race_comparison = _build_qualifying_race_comparison_rows(
        lap_rows,
        generated_at,
    )
    session_summaries = _build_session_summary_rows(
        race_pace_rankings=race_pace_rankings,
        pace_degradation=pace_degradation,
        tire_windows=tire_windows,
        sector_dominance=sector_dominance,
        generated_at=generated_at,
    )
    driver_reports = _build_driver_report_rows(
        consistency_scores=consistency_scores,
        tire_windows=tire_windows,
        pace_degradation=pace_degradation,
        sector_dominance=sector_dominance,
        strategy_opportunities=strategy_opportunities,
        generated_at=generated_at,
    )
    strategy_summaries = _build_strategy_summary_rows(
        strategy_opportunities=strategy_opportunities,
        stint_strength=stint_strength,
        tire_windows=tire_windows,
        generated_at=generated_at,
    )
    race_trends = _build_race_trend_rows(
        pace_degradation=pace_degradation,
        race_pace_rankings=race_pace_rankings,
        qualifying_race_comparison=qualifying_race_comparison,
        generated_at=generated_at,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "pace_degradation": output_dir / "intelligence_pace_degradation.parquet",
        "sector_dominance": output_dir / "intelligence_sector_dominance.parquet",
        "consistency_scores": output_dir / "intelligence_consistency_scores.parquet",
        "tire_windows": output_dir / "intelligence_tire_performance_windows.parquet",
        "strategy_opportunities": output_dir / "intelligence_strategy_opportunities.parquet",
        "stint_strength": output_dir / "intelligence_stint_strength.parquet",
        "race_pace_rankings": output_dir / "intelligence_race_pace_rankings.parquet",
        "qualifying_race_comparison": output_dir
        / "intelligence_qualifying_race_comparison.parquet",
        "session_summaries": output_dir / "intelligence_session_summaries.parquet",
        "driver_reports": output_dir / "intelligence_driver_reports.parquet",
        "strategy_summaries": output_dir / "intelligence_strategy_summaries.parquet",
        "race_trends": output_dir / "intelligence_race_trends.parquet",
    }
    _write_rows(
        outputs["pace_degradation"],
        pace_degradation,
        _schema(INTELLIGENCE_PACE_DEGRADATION_COLUMNS),
    )
    _write_rows(
        outputs["sector_dominance"],
        sector_dominance,
        _schema(INTELLIGENCE_SECTOR_DOMINANCE_COLUMNS),
    )
    _write_rows(
        outputs["consistency_scores"],
        consistency_scores,
        _schema(INTELLIGENCE_CONSISTENCY_SCORES_COLUMNS),
    )
    _write_rows(outputs["tire_windows"], tire_windows, _schema(INTELLIGENCE_TIRE_WINDOWS_COLUMNS))
    _write_rows(
        outputs["strategy_opportunities"],
        strategy_opportunities,
        _schema(INTELLIGENCE_STRATEGY_OPPORTUNITIES_COLUMNS),
    )
    _write_rows(
        outputs["stint_strength"],
        stint_strength,
        _schema(INTELLIGENCE_STINT_STRENGTH_COLUMNS),
    )
    _write_rows(
        outputs["race_pace_rankings"],
        race_pace_rankings,
        _schema(INTELLIGENCE_RACE_PACE_RANKINGS_COLUMNS),
    )
    _write_rows(
        outputs["qualifying_race_comparison"],
        qualifying_race_comparison,
        _schema(INTELLIGENCE_QUALIFYING_RACE_COMPARISON_COLUMNS),
    )
    _write_rows(
        outputs["session_summaries"],
        session_summaries,
        _schema(INTELLIGENCE_SESSION_SUMMARY_COLUMNS),
    )
    _write_rows(
        outputs["driver_reports"],
        driver_reports,
        _schema(INTELLIGENCE_DRIVER_REPORT_COLUMNS),
    )
    _write_rows(
        outputs["strategy_summaries"],
        strategy_summaries,
        _schema(INTELLIGENCE_STRATEGY_SUMMARY_COLUMNS),
    )
    _write_rows(outputs["race_trends"], race_trends, _schema(INTELLIGENCE_RACE_TREND_COLUMNS))
    return outputs


def _build_pace_degradation_rows(
    pace_rows: list[dict[str, object]], generated_at: str
) -> list[dict[str, object]]:
    grouped: dict[tuple[int, int, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in pace_rows:
        grouped[_driver_session_key_with_gp(row)].append(row)

    records = []
    for key, rows in grouped.items():
        ordered = sorted(rows, key=lambda row: int(row["lap_number"]))
        first = int(ordered[0]["rolling_avg_lap_time_ms"])
        last = int(ordered[-1]["rolling_avg_lap_time_ms"])
        lap_span = max(len(ordered) - 1, 1)
        slope = round((last - first) / lap_span)
        delta_change = int(ordered[-1]["delta_to_fastest_ms"]) - int(
            ordered[0]["delta_to_fastest_ms"]
        )
        if slope >= 180:
            level = "high"
        elif slope >= 80:
            level = "medium"
        else:
            level = "low"
        season, round_number, grand_prix, session, driver_code = key
        records.append(
            {
                "season": season,
                "round": round_number,
                "grand_prix": grand_prix,
                "session": session,
                "driver_code": driver_code,
                "pace_slope_ms_per_lap": slope,
                "degradation_level": level,
                "supporting_delta_ms": delta_change,
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_sector_dominance_rows(
    sector_rows: list[dict[str, object]], generated_at: str
) -> list[dict[str, object]]:
    grouped: dict[tuple[int, int, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in sector_rows:
        grouped[_driver_session_key_with_gp(row)].append(row)

    records = []
    for key, rows in grouped.items():
        sector_stats = []
        for sector_name in ("sector_1_delta_ms", "sector_2_delta_ms", "sector_3_delta_ms"):
            valid = [int(row[sector_name]) for row in rows if row.get(sector_name) is not None]
            if not valid:
                sector_stats.append((sector_name, 9999.0, 0))
                continue
            sector_stats.append(
                (
                    sector_name,
                    sum(valid) / len(valid),
                    sum(1 for value in valid if value <= 40),
                )
            )
        dominant = min(sector_stats, key=lambda item: (item[1], -item[2], item[0]))
        avg_advantage = -round(float(dominant[1]))
        win_count = int(dominant[2])
        if win_count >= max(len(rows) // 2, 2):
            label = "commanding"
        elif win_count >= 1:
            label = "competitive"
        else:
            label = "balanced"
        season, round_number, grand_prix, session, driver_code = key
        records.append(
            {
                "season": season,
                "round": round_number,
                "grand_prix": grand_prix,
                "session": session,
                "driver_code": driver_code,
                "dominant_sector": dominant[0].replace("_delta_ms", ""),
                "sector_win_count": win_count,
                "avg_sector_advantage_ms": avg_advantage,
                "dominance_label": label,
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_consistency_score_rows(
    consistency_rows: list[dict[str, object]], generated_at: str
) -> list[dict[str, object]]:
    records = []
    for row in consistency_rows:
        consistency_index = float(row["consistency_index"])
        stddev = int(row["lap_time_stddev_ms"])
        reliability_score = round((consistency_index * 100.0) - (stddev / 50.0), 2)
        if consistency_index >= 0.9:
            band = "elite"
        elif consistency_index >= 0.8:
            band = "strong"
        elif consistency_index >= 0.7:
            band = "volatile"
        else:
            band = "fragile"
        records.append(
            {
                "season": int(row["season"]),
                "round": int(row["round"]),
                "grand_prix": str(row["grand_prix"]),
                "session": str(row["session"]),
                "driver_code": str(row["driver_code"]),
                "consistency_index": consistency_index,
                "consistency_band": band,
                "lap_time_stddev_ms": stddev,
                "reliability_score": reliability_score,
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_tire_window_rows(
    lap_rows: list[dict[str, object]], generated_at: str
) -> list[dict[str, object]]:
    grouped: dict[tuple[int, int, str, str, str, int | None], list[dict[str, object]]] = (
        defaultdict(list)
    )
    for row in lap_rows:
        grouped[
            (
                int(row["season"]),
                int(row["round"]),
                str(row["grand_prix"]),
                str(row["session"]),
                str(row["driver_code"]),
                _int_or_none(row.get("stint")),
            )
        ].append(row)

    records = []
    for (season, round_number, grand_prix, session, driver_code, stint), rows in grouped.items():
        ordered = sorted(rows, key=lambda row: int(row["lap_number"]))
        best_window = None
        for index in range(len(ordered)):
            window = ordered[index : index + 2]
            if not window:
                continue
            average = round(sum(int(item["lap_time_ms"]) for item in window) / len(window))
            candidate = (average, int(window[0]["lap_number"]), int(window[-1]["lap_number"]))
            if best_window is None or candidate < best_window:
                best_window = candidate
        if best_window is None:
            continue
        avg_delta = round(sum(int(item["delta_to_fastest_ms"]) for item in ordered) / len(ordered))
        if avg_delta <= 250:
            quality = "attack"
        elif avg_delta <= 700:
            quality = "usable"
        else:
            quality = "fade"
        records.append(
            {
                "season": season,
                "round": round_number,
                "grand_prix": grand_prix,
                "session": session,
                "driver_code": driver_code,
                "stint": stint,
                "compound": _first_text(ordered, "compound"),
                "performance_window_start_lap": best_window[1],
                "performance_window_end_lap": best_window[2],
                "window_quality": quality,
                "window_avg_lap_time_ms": best_window[0],
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_strategy_opportunity_rows(
    *,
    tire_rows: list[dict[str, object]],
    pace_rows: list[dict[str, object]],
    generated_at: str,
) -> list[dict[str, object]]:
    best_pace_by_session: dict[tuple[int, int, str, str], tuple[str, int]] = {}
    for row in pace_rows:
        key = (
            int(row["season"]),
            int(row["round"]),
            str(row["grand_prix"]),
            str(row["session"]),
        )
        candidate = (str(row["driver_code"]), int(row["rolling_avg_lap_time_ms"]))
        current = best_pace_by_session.get(key)
        if current is None or candidate[1] < current[1]:
            best_pace_by_session[key] = candidate

    records = []
    for row in tire_rows:
        session_key = (
            int(row["season"]),
            int(row["round"]),
            str(row["grand_prix"]),
            str(row["session"]),
        )
        if str(row["session"]) != "R":
            continue
        reference = best_pace_by_session.get(session_key)
        if reference is None or reference[0] == str(row["driver_code"]):
            continue
        delta = int(row["avg_lap_time_ms"]) - reference[1]
        if delta <= 0:
            continue
        if delta <= 400:
            opportunity_type = "overcut"
            label = "late-stop upside"
        elif delta <= 1200:
            opportunity_type = "undercut"
            label = "pit-window attack"
        else:
            opportunity_type = "offset"
            label = "needs aggressive offset"
        records.append(
            {
                "season": int(row["season"]),
                "round": int(row["round"]),
                "grand_prix": str(row["grand_prix"]),
                "session": str(row["session"]),
                "driver_code": str(row["driver_code"]),
                "opportunity_type": opportunity_type,
                "reference_driver": reference[0],
                "opportunity_delta_ms": delta,
                "window_start_lap": int(row["start_lap"]),
                "window_end_lap": int(row["end_lap"]),
                "opportunity_label": label,
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_stint_strength_rows(
    tire_rows: list[dict[str, object]], generated_at: str
) -> list[dict[str, object]]:
    records = []
    for row in tire_rows:
        avg_delta = int(row["avg_delta_to_fastest_ms"])
        top_speed = _int_or_none(row.get("avg_top_speed_kph")) or 0
        score = round(max(0.0, 100.0 - (avg_delta / 15.0) + ((top_speed - 300) / 3.0)), 2)
        if score >= 85:
            label = "dominant"
        elif score >= 70:
            label = "competitive"
        elif score >= 55:
            label = "holding"
        else:
            label = "fragile"
        records.append(
            {
                "season": int(row["season"]),
                "round": int(row["round"]),
                "grand_prix": str(row["grand_prix"]),
                "session": str(row["session"]),
                "driver_code": str(row["driver_code"]),
                "stint": _int_or_none(row.get("stint")),
                "compound": row.get("compound"),
                "strength_score": score,
                "strength_label": label,
                "avg_delta_to_fastest_ms": avg_delta,
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_race_pace_ranking_rows(
    *,
    consistency_rows: list[dict[str, object]],
    baseline_rows: list[dict[str, object]],
    generated_at: str,
) -> list[dict[str, object]]:
    baseline_map = {_driver_session_key(row): row for row in baseline_rows}
    grouped: dict[tuple[int, int, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in consistency_rows:
        if str(row["session"]) != "R":
            continue
        baseline = baseline_map.get(_driver_session_key(row))
        score = (float(row["consistency_index"]) * 100.0) - (
            int(row["avg_delta_to_fastest_ms"]) / 20.0
        )
        if baseline is not None:
            score += float(baseline["score"]) * 10.0
        grouped[_session_key_with_gp(row)].append(
            {
                "driver_code": str(row["driver_code"]),
                "race_pace_score": round(score, 2),
                "pace_gap_ms": int(row["avg_delta_to_fastest_ms"]),
                "ranking_reason": (
                    f"Consistency {float(row['consistency_index']):.3f} with "
                    f"{int(row['avg_delta_to_fastest_ms'])}ms average gap."
                ),
            }
        )

    records = []
    for (season, round_number, grand_prix, session), rows in grouped.items():
        ordered = sorted(
            rows, key=lambda row: (-float(row["race_pace_score"]), str(row["driver_code"]))
        )
        leader_score = float(ordered[0]["race_pace_score"]) if ordered else 0.0
        for rank, row in enumerate(ordered, start=1):
            records.append(
                {
                    "season": season,
                    "round": round_number,
                    "grand_prix": grand_prix,
                    "session": session,
                    "rank": rank,
                    "driver_code": row["driver_code"],
                    "race_pace_score": row["race_pace_score"],
                    "pace_gap_ms": round(leader_score - float(row["race_pace_score"]), 2),
                    "ranking_reason": row["ranking_reason"],
                    "intelligence_generated_at": generated_at,
                }
            )
    return records


def _build_qualifying_race_comparison_rows(
    lap_rows: list[dict[str, object]], generated_at: str
) -> list[dict[str, object]]:
    best_laps: dict[tuple[int, int, str, str], int] = {}
    grand_prix_by_driver_round: dict[tuple[int, int, str], str] = {}
    for row in lap_rows:
        driver_key = (
            int(row["season"]),
            int(row["round"]),
            str(row["session"]),
            str(row["driver_code"]),
        )
        best = best_laps.get(driver_key)
        lap_time = int(row["lap_time_ms"])
        if best is None or lap_time < best:
            best_laps[driver_key] = lap_time
        grand_prix_by_driver_round[
            (int(row["season"]), int(row["round"]), str(row["driver_code"]))
        ] = str(row["grand_prix"])

    records = []
    for (season, round_number, driver_code_key), grand_prix in grand_prix_by_driver_round.items():
        qualifying_best = best_laps.get((season, round_number, "Q", driver_code_key))
        race_best = best_laps.get((season, round_number, "R", driver_code_key))
        if qualifying_best is None or race_best is None:
            continue
        gap = race_best - qualifying_best
        if gap <= 1800:
            label = "converted cleanly"
        elif gap <= 3200:
            label = "balanced shift"
        else:
            label = "race trim heavy"
        records.append(
            {
                "season": season,
                "round": round_number,
                "grand_prix": grand_prix,
                "driver_code": driver_code_key,
                "qualifying_best_lap_ms": qualifying_best,
                "race_best_lap_ms": race_best,
                "qualifying_to_race_gap_ms": gap,
                "conversion_label": label,
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_session_summary_rows(
    *,
    race_pace_rankings: list[dict[str, object]],
    pace_degradation: list[dict[str, object]],
    tire_windows: list[dict[str, object]],
    sector_dominance: list[dict[str, object]],
    generated_at: str,
) -> list[dict[str, object]]:
    records = []
    rankings_by_session: dict[tuple[int, int, str, str], list[dict[str, object]]] = defaultdict(
        list
    )
    degradation_by_session: dict[tuple[int, int, str, str], list[dict[str, object]]] = defaultdict(
        list
    )
    windows_by_session: dict[tuple[int, int, str, str], list[dict[str, object]]] = defaultdict(list)
    sectors_by_session: dict[tuple[int, int, str, str], list[dict[str, object]]] = defaultdict(list)

    for row in race_pace_rankings:
        rankings_by_session[_session_key_with_gp(row)].append(row)
    for row in pace_degradation:
        degradation_by_session[_session_key_with_gp(row)].append(row)
    for row in tire_windows:
        windows_by_session[_session_key_with_gp(row)].append(row)
    for row in sector_dominance:
        sectors_by_session[_session_key_with_gp(row)].append(row)

    all_keys = (
        set(rankings_by_session)
        | set(degradation_by_session)
        | set(windows_by_session)
        | set(sectors_by_session)
    )
    for key in sorted(all_keys):
        season, round_number, grand_prix, session = key
        rankings = sorted(rankings_by_session.get(key, []), key=lambda row: int(row["rank"]))
        degradations = sorted(
            degradation_by_session.get(key, []),
            key=lambda row: (-int(row["pace_slope_ms_per_lap"]), str(row["driver_code"])),
        )
        windows = windows_by_session.get(key, [])
        sectors = sectors_by_session.get(key, [])
        if rankings:
            leader = rankings[0]
            records.append(
                {
                    "season": season,
                    "round": round_number,
                    "grand_prix": grand_prix,
                    "session": session,
                    "summary_type": "driver_performance",
                    "headline": f"{leader['driver_code']} leads the race-pace model",
                    "detail": str(leader["ranking_reason"]),
                    "importance_score": 98.0,
                    "intelligence_generated_at": generated_at,
                }
            )
        if degradations:
            strongest = degradations[0]
            records.append(
                {
                    "season": season,
                    "round": round_number,
                    "grand_prix": grand_prix,
                    "session": session,
                    "summary_type": "pace_evolution",
                    "headline": f"{strongest['driver_code']} shows the sharpest degradation",
                    "detail": (
                        f"Slope {int(strongest['pace_slope_ms_per_lap'])} ms/lap with "
                        f"{strongest['degradation_level']} fade."
                    ),
                    "importance_score": 87.0,
                    "intelligence_generated_at": generated_at,
                }
            )
        if windows:
            attack_window = min(windows, key=lambda row: int(row["window_avg_lap_time_ms"]))
            records.append(
                {
                    "season": season,
                    "round": round_number,
                    "grand_prix": grand_prix,
                    "session": session,
                    "summary_type": "tire_behavior",
                    "headline": f"{attack_window['driver_code']} unlocked the best tire window",
                    "detail": (
                        f"{attack_window['compound']} stint "
                        f"{attack_window['stint']} peaked on laps "
                        f"{attack_window['performance_window_start_lap']}-"
                        f"{attack_window['performance_window_end_lap']}."
                    ),
                    "importance_score": 81.0,
                    "intelligence_generated_at": generated_at,
                }
            )
        if sectors:
            best_sector = max(
                sectors,
                key=lambda row: (int(row["sector_win_count"]), int(row["avg_sector_advantage_ms"])),
            )
            records.append(
                {
                    "season": season,
                    "round": round_number,
                    "grand_prix": grand_prix,
                    "session": session,
                    "summary_type": "strategic_observation",
                    "headline": (
                        f"{best_sector['driver_code']} owns " f"{best_sector['dominant_sector']}"
                    ),
                    "detail": (
                        f"{best_sector['sector_win_count']} near-best executions and "
                        f"{best_sector['dominance_label']} sector control."
                    ),
                    "importance_score": 76.0,
                    "intelligence_generated_at": generated_at,
                }
            )
    return sorted(records, key=lambda row: (-float(row["importance_score"]), str(row["headline"])))


def _build_driver_report_rows(
    *,
    consistency_scores: list[dict[str, object]],
    tire_windows: list[dict[str, object]],
    pace_degradation: list[dict[str, object]],
    sector_dominance: list[dict[str, object]],
    strategy_opportunities: list[dict[str, object]],
    generated_at: str,
) -> list[dict[str, object]]:
    tire_by_driver = {_driver_session_key_with_gp(row): row for row in tire_windows}
    degradation_by_driver = {_driver_session_key_with_gp(row): row for row in pace_degradation}
    sector_by_driver = {_driver_session_key_with_gp(row): row for row in sector_dominance}
    strategy_by_driver = {_driver_session_key_with_gp(row): row for row in strategy_opportunities}

    records = []
    for consistency in consistency_scores:
        key = _driver_session_key_with_gp(consistency)
        tire = tire_by_driver.get(key)
        degradation = degradation_by_driver.get(key)
        sector = sector_by_driver.get(key)
        strategy = strategy_by_driver.get(key)
        performance_summary = (
            f"{consistency['driver_code']} delivered a {consistency['consistency_band']} execution "
            f"with reliability score {float(consistency['reliability_score']):.1f}."
        )
        strategy_summary = (
            f"Best strategic lever: {strategy['opportunity_label']} "
            f"versus {strategy['reference_driver']}."
            if strategy
            else "No clear undercut/overcut edge was detected from the stint profile."
        )
        tire_summary = (
            f"{tire['compound']} reached its best window on laps "
            f"{tire['performance_window_start_lap']}-{tire['performance_window_end_lap']}."
            if tire
            else "Tire performance window could not be isolated."
        )
        trend_summary = (
            f"Pace degradation remained {degradation['degradation_level']} at "
            f"{degradation['pace_slope_ms_per_lap']} ms/lap, with "
            f"{sector['dominant_sector']} as the anchor."
            if degradation and sector
            else "Trend signal is partial for this driver."
        )
        records.append(
            {
                "season": int(consistency["season"]),
                "round": int(consistency["round"]),
                "grand_prix": str(consistency["grand_prix"]),
                "session": str(consistency["session"]),
                "driver_code": str(consistency["driver_code"]),
                "report_title": f"{consistency['driver_code']} intelligence report",
                "performance_summary": performance_summary,
                "strategy_summary": strategy_summary,
                "tire_summary": tire_summary,
                "trend_summary": trend_summary,
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_strategy_summary_rows(
    *,
    strategy_opportunities: list[dict[str, object]],
    stint_strength: list[dict[str, object]],
    tire_windows: list[dict[str, object]],
    generated_at: str,
) -> list[dict[str, object]]:
    strength_by_driver = {_driver_session_key_with_gp(row): row for row in stint_strength}
    windows_by_driver = {_driver_session_key_with_gp(row): row for row in tire_windows}

    records = []
    for opportunity in strategy_opportunities:
        strength = strength_by_driver.get(_driver_session_key_with_gp(opportunity))
        window = windows_by_driver.get(_driver_session_key_with_gp(opportunity))
        detail = (
            f"Window {opportunity['window_start_lap']}-{opportunity['window_end_lap']} "
            f"projects {opportunity['opportunity_type']} pressure. "
        )
        if strength:
            detail += (
                f"Stint is {strength['strength_label']} at score "
                f"{float(strength['strength_score']):.1f}. "
            )
        if window:
            detail += (
                f"Best tyre phase lands on laps "
                f"{window['performance_window_start_lap']}-{window['performance_window_end_lap']}."
            )
        records.append(
            {
                "season": int(opportunity["season"]),
                "round": int(opportunity["round"]),
                "grand_prix": str(opportunity["grand_prix"]),
                "session": str(opportunity["session"]),
                "driver_code": str(opportunity["driver_code"]),
                "strategy_headline": (
                    f"{opportunity['driver_code']} has a " f"{opportunity['opportunity_label']}"
                ),
                "strategy_detail": detail.strip(),
                "opportunity_type": str(opportunity["opportunity_type"]),
                "opportunity_label": str(opportunity["opportunity_label"]),
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _build_race_trend_rows(
    *,
    pace_degradation: list[dict[str, object]],
    race_pace_rankings: list[dict[str, object]],
    qualifying_race_comparison: list[dict[str, object]],
    generated_at: str,
) -> list[dict[str, object]]:
    ranking_by_driver = {_driver_session_key_with_gp(row): row for row in race_pace_rankings}
    quali_race_by_driver_round = {
        (int(row["season"]), int(row["round"]), str(row["driver_code"])): row
        for row in qualifying_race_comparison
    }

    records = []
    for degradation in pace_degradation:
        key = _driver_session_key_with_gp(degradation)
        ranking = ranking_by_driver.get(key)
        conversion = quali_race_by_driver_round.get(
            (int(degradation["season"]), int(degradation["round"]), str(degradation["driver_code"]))
        )
        detail = (
            f"Degradation ran at {degradation['pace_slope_ms_per_lap']} ms/lap and "
            f"finished as {degradation['degradation_level']} fade."
        )
        if ranking:
            detail += f" Race pace ranking sat P{ranking['rank']}."
        if conversion:
            detail += f" Q-to-race conversion was {conversion['conversion_label']}."
        records.append(
            {
                "season": int(degradation["season"]),
                "round": int(degradation["round"]),
                "grand_prix": str(degradation["grand_prix"]),
                "session": str(degradation["session"]),
                "driver_code": str(degradation["driver_code"]),
                "trend_category": "pace_evolution",
                "trend_headline": f"{degradation['driver_code']} trend profile",
                "trend_detail": detail,
                "intelligence_generated_at": generated_at,
            }
        )
    return records


def _read_rows(path: Path, required_columns: set[str], label: str) -> list[dict[str, object]]:
    table = pq.read_table(path)
    missing = required_columns.difference(table.schema.names)
    if missing:
        raise ValueError(f"Missing required {label} columns: {', '.join(sorted(missing))}")
    rows = table.to_pylist()
    if "driver_code" in required_columns:
        return _valid_rows_with_driver_codes(rows, label=label)
    return rows


def _write_rows(path: Path, rows: list[dict[str, object]], schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), path)


def _valid_rows_with_driver_codes(
    rows: list[dict[str, object]],
    *,
    label: str,
) -> list[dict[str, object]]:
    valid_rows: list[dict[str, object]] = []
    malformed: list[int] = []
    for index, row in enumerate(rows):
        driver_code = row.get("driver_code")
        if driver_code is None or not str(driver_code).strip():
            malformed.append(index)
            continue
        row["driver_code"] = str(driver_code).strip().upper()
        valid_rows.append(row)

    if malformed:
        logger.warning(
            "dropped malformed intelligence input rows with missing driver_code",
            extra={
                "dataset": label,
                "malformed_row_indexes": malformed[:10],
                "malformed_row_count": len(malformed),
            },
        )
    return valid_rows


def _schema(columns: list[str]) -> pa.Schema:
    types: dict[str, pa.DataType] = {
        "season": pa.int64(),
        "round": pa.int64(),
        "grand_prix": pa.string(),
        "session": pa.string(),
        "driver_code": pa.string(),
        "rank": pa.int64(),
        "score": pa.float64(),
        "insight_generated_at": pa.string(),
        "pace_slope_ms_per_lap": pa.int64(),
        "degradation_level": pa.string(),
        "supporting_delta_ms": pa.int64(),
        "intelligence_generated_at": pa.string(),
        "dominant_sector": pa.string(),
        "sector_win_count": pa.int64(),
        "avg_sector_advantage_ms": pa.int64(),
        "dominance_label": pa.string(),
        "consistency_index": pa.float64(),
        "consistency_band": pa.string(),
        "lap_time_stddev_ms": pa.int64(),
        "reliability_score": pa.float64(),
        "stint": pa.int64(),
        "compound": pa.string(),
        "performance_window_start_lap": pa.int64(),
        "performance_window_end_lap": pa.int64(),
        "window_quality": pa.string(),
        "window_avg_lap_time_ms": pa.int64(),
        "opportunity_type": pa.string(),
        "reference_driver": pa.string(),
        "opportunity_delta_ms": pa.int64(),
        "window_start_lap": pa.int64(),
        "window_end_lap": pa.int64(),
        "opportunity_label": pa.string(),
        "strength_score": pa.float64(),
        "strength_label": pa.string(),
        "avg_delta_to_fastest_ms": pa.int64(),
        "race_pace_score": pa.float64(),
        "pace_gap_ms": pa.float64(),
        "ranking_reason": pa.string(),
        "qualifying_best_lap_ms": pa.int64(),
        "race_best_lap_ms": pa.int64(),
        "qualifying_to_race_gap_ms": pa.int64(),
        "conversion_label": pa.string(),
        "summary_type": pa.string(),
        "headline": pa.string(),
        "detail": pa.string(),
        "importance_score": pa.float64(),
        "report_title": pa.string(),
        "performance_summary": pa.string(),
        "strategy_summary": pa.string(),
        "tire_summary": pa.string(),
        "trend_summary": pa.string(),
        "strategy_headline": pa.string(),
        "strategy_detail": pa.string(),
        "trend_category": pa.string(),
        "trend_headline": pa.string(),
        "trend_detail": pa.string(),
    }
    return pa.schema([(column, types[column]) for column in columns])


def _top_driver_schema() -> pa.Schema:
    return _schema(INSIGHT_SESSION_TOP_DRIVERS_COLUMNS)


def _session_key(row: dict[str, object]) -> tuple[int, int, str]:
    return (int(row["season"]), int(row["round"]), str(row["session"]))


def _session_key_with_gp(row: dict[str, object]) -> tuple[int, int, str, str]:
    return (int(row["season"]), int(row["round"]), str(row["grand_prix"]), str(row["session"]))


def _driver_session_key(row: dict[str, object]) -> tuple[int, int, str, str]:
    return (int(row["season"]), int(row["round"]), str(row["session"]), str(row["driver_code"]))


def _driver_session_key_with_gp(row: dict[str, object]) -> tuple[int, int, str, str, str]:
    return (
        int(row["season"]),
        int(row["round"]),
        str(row["grand_prix"]),
        str(row["session"]),
        str(row["driver_code"]),
    )


def _driver_session_key_with_gp_stint(
    row: dict[str, object],
) -> tuple[int, int, str, str, str, int | None]:
    return (
        int(row["season"]),
        int(row["round"]),
        str(row["grand_prix"]),
        str(row["session"]),
        str(row["driver_code"]),
        _int_or_none(row.get("stint")),
    )


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _first_text(rows: list[dict[str, object]], field: str) -> str | None:
    for row in rows:
        value = row.get(field)
        if value is not None and str(value).strip():
            return str(value)
    return None
