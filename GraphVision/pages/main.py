import reflex as rx

from ..components import (
    plot_layout,
)

def main_page() -> rx.Component:
    return rx.box(
        plot_layout(),
        width="100vw",
        height="100vh",
        bg="gray",
    )
