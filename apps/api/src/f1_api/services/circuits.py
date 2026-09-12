from __future__ import annotations

import fastf1

from f1_api.services.circuit_catalog import ENGINEERING_METADATA


def get_circuit_metadata(year: int, round_number: int) -> dict:
    """Combine FastF1 schedule metadata with engineering metadata."""

    schedule = fastf1.get_event_schedule(year)
    event = schedule[schedule["RoundNumber"] == round_number]

    if event.empty:
        raise ValueError(
            f"No event found for season={year}, round={round_number}"
        )

    event = event.iloc[0]

    event_name = event["EventName"]

    engineering = ENGINEERING_METADATA.get(event_name)

    if engineering is None:
        raise ValueError(
            f"Engineering metadata not available for '{event_name}'"
        )

    return {
        "season": year,
        "round": round_number,
        "grand_prix": event_name,
        "official_name": event["OfficialEventName"],
        "country": event["Country"],
        "location": event["Location"],
        "track_length_km": engineering.track_length_km,
        "corners": engineering.corners,
        "drs_zones": engineering.drs_zones,
        "clockwise": engineering.clockwise,
        "sector_count": engineering.sector_count,
        "speed_trap_kmh": engineering.speed_trap_kmh,
    }