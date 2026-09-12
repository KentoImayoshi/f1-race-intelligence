from __future__ import annotations

import requests
import streamlit as st

from f1_core.config import settings


API_BASE_URL = settings.api_base_url.rstrip("/") + settings.api_v1_prefix


@st.cache_data(show_spinner=False)
def get_circuit_metadata(year: int, round_number: int) -> dict:
    response = requests.get(
        f"{API_BASE_URL}/circuits",
        params={"year": year, "round": round_number},
        timeout=10,
    )

    response.raise_for_status()

    return response.json()