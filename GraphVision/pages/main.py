import reflex as rx

from ..components import (
    plot_layout,
    control_panel,
    top_menu,
)
from ..models import GraphState as State
from ..models.busy_state import BusyState


def main_page() -> rx.Component:
    return rx.vstack(
        top_menu(),
        rx.flex(
            rx.box(
                control_panel(),
                width="30%",
            ),
            rx.spacer(),
            rx.box(
                plot_layout(),
                width="70%",
            ),
            width="100%",
            flex="1",
            spacing="1",
            bg="white",
        ),
        rx.cond(
            BusyState.is_busy,
            rx.box(
                rx.vstack(
                    rx.spinner(size="3"),
                    rx.text(BusyState.message, color="white"),
                    align="center",
                    spacing="2",
                ),
                position="fixed",
                top="0",
                left="0",
                right="0",
                bottom="0",
                background="rgba(0,0,0,0.4)",
                display="flex",
                align_items="center",
                justify_content="center",
                z_index="1000",
            ),
            rx.fragment(),
        ),
        width="100vw",
        height="100vh",
        spacing="0",
        bg="white",
    )
