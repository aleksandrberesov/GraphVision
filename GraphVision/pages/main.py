import reflex as rx
from rxconfig import config

from ..components import (
    plot_layout,
)

points = [
    {"x": 40, "y": 20, "label": "P1"},
    {"x": 100, "y": 60, "label": "P2"},
    {"x": 200, "y": 120, "label": "P3"},
    {"x": 300, "y": 420, "label": "P4"},
    {"x": 400, "y": 220, "label": "P5"},
    {"x": 600, "y": 20, "label": "P6"},
]

def main_page() -> rx.Component:
    return rx.box(
        plot_layout(points),
        width="100vw",
        height="100vh",
        bg="gray",
    )
