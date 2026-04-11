import reflex as rx

from ..components import (
    plot_layout, 
    control_panel
)

def main_page() -> rx.Component:
    return rx.flex(
        rx.box(
            control_panel(),
            width="30%",
        ),
        rx.spacer(),
        rx.box(
            plot_layout(), 
            width="70%",   
        ),
        width="100vw",
        height="100vh",
        spacing="1",
        bg="white",
    )
