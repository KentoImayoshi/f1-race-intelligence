from __future__ import annotations

import streamlit as st

from f1_dashboard.client.api import (
    get_circuit_metadata,
    get_track_coordinates,
)
from f1_dashboard.components.circuit_map import render as render_circuit_map


def render(year: int, selected_event, session_code: str) -> None:
    """
    Circuit Intelligence page.

    Uses the shared dashboard context (year, selected event and session)
    to fetch engineering metadata and telemetry from the FastAPI backend.
    """

    metadata, metadata_error = get_circuit_metadata(
        year=year,
        round_number=selected_event.round_number,
    )

    if metadata_error:
        st.error(metadata_error)
        return

    st.title(f"🏁 {metadata['grand_prix']}")
    st.caption(
        f"{metadata['location']} • {metadata['country']} • Session: {session_code}"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Track Length", f"{metadata['track_length_km']} km")
    c2.metric("Corners", metadata["corners"])
    c3.metric("DRS Zones", metadata["drs_zones"])
    c4.metric("Speed Trap", f"{metadata['speed_trap_kmh']} km/h")

    st.divider()

    left, right = st.columns([2.3, 1])

    with left:
        st.subheader("Circuit Map")

        with st.spinner("Loading circuit telemetry..."):
            payload, telemetry_error = get_track_coordinates(
                year=year,
                round_number=selected_event.round_number,
                session="R",
            )

        if telemetry_error:
            st.error(telemetry_error)   
        else:
            render_circuit_map(payload["track"])    

    with right:
        st.subheader("Engineering Overview")

        st.metric(
            "Direction",
            "Clockwise" if metadata["clockwise"] else "Anti-clockwise",
        )
        st.metric("Sectors", metadata["sector_count"])

        st.info(
            """
            **Heavy braking:** Turns 1, 4, 8 and 10.

            **Tire characteristic:** High rear tire degradation.

            **DRS configuration:** Three DRS zones available.
            """
        )

    st.divider()

    st.subheader("Telemetry Explorer")

    t1, t2, t3 = st.columns(3)

    with t1:
        with st.container(border=True):
            st.caption("Speed Trace")
            st.write("Coming in Sprint 2.3")

    with t2:
        with st.container(border=True):
            st.caption("Throttle Trace")
            st.write("Coming in Sprint 2.3")

    with t3:
        with st.container(border=True):
            st.caption("Brake Trace")
            st.write("Coming in Sprint 2.3")