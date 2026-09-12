from __future__ import annotations

import streamlit as st

from f1_dashboard.client.api import get_circuit_metadata


def render(year: int, selected_event, session_code: str):
    """
    Circuit Intelligence page.

    Uses the shared dashboard context (year, selected event and session)
    to fetch engineering metadata from the FastAPI backend.
    """

    metadata = get_circuit_metadata(
        year=year,
        round_number=selected_event.round_number,
    )

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

        with st.container(border=True):
            st.markdown(
                """
                <div style="
                    height:420px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    color:#8899aa;
                    font-size:18px;
                ">
                    SVG Circuit Map arriving in Sprint 2.3
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        st.subheader("Engineering Overview")

        st.metric("Direction", "Clockwise" if metadata["clockwise"] else "Anti-clockwise")
        st.metric("Sectors", metadata["sector_count"])

        st.info(
            """
            Heavy braking into Turn 1, Turn 4, Turn 8 and Turn 10.

            High rear tire degradation.

            Three DRS zones available.
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