from __future__ import annotations

import streamlit.components.v1 as components


def render(track_points: list[dict]) -> None:
    if not track_points:
        components.html(
            """
            <div style="
                height:640px;
                display:flex;
                align-items:center;
                justify-content:center;
                color:#7B8794;
                background:#081018;
                border-radius:20px;
                font-family:Inter,sans-serif;">
                No telemetry available.
            </div>
            """,
            height=640,
        )
        return

    xs = [p["x"] for p in track_points]
    ys = [p["y"] for p in track_points]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    track_width = max(max_x - min_x, 1)
    track_height = max(max_y - min_y, 1)

    scale = 560 / max(track_width, track_height)

    svg_points = []

    for p in track_points:
        x = (p["x"] - min_x) * scale + 40
        y = (max_y - p["y"]) * scale + 40  # inverte eixo Y
        svg_points.append(f"{x:.2f},{y:.2f}")

    polyline = " ".join(svg_points)

    svg = f"""
    <svg
        width="640"
        height="640"
        viewBox="0 0 640 640"
        xmlns="http://www.w3.org/2000/svg"
        style="display:block;background:#081018;border-radius:20px;"
    >
        <rect width="640" height="640" rx="20" fill="#081018"/>

        <polyline
            points="{polyline}"
            fill="none"
            stroke="#FF5B4D"
            stroke-width="5"
            stroke-linecap="round"
            stroke-linejoin="round"
        />
    </svg>
    """

    components.html(svg, height=640, scrolling=False)