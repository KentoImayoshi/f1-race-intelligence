from __future__ import annotations

import requests
import streamlit as st

from f1_core.config import settings

API_BASE_URL = settings.api_base_url.rstrip("/") + settings.api_v1_prefix


def _fetch_json(path: str, params: dict | None = None):
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        return response.json(), None

    except requests.RequestException as exc:
        return None, str(exc)


@st.cache_data(show_spinner=False)
def get_circuit_metadata(year: int, round_number: int):
    return _fetch_json(
        "/circuits",
        {
            "year": year,
            "round": round_number,
        },
    )


@st.cache_data(show_spinner=False)
def get_track_coordinates(
    year: int,
    round_number: int,
    session: str = "R",
):
    return _fetch_json(
        "/circuits/track",
        {
            "year": year,
            "round": round_number,
            "session": session,
        },
    )