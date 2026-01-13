import reflex as rx

from ..elements import button_box_drawer
from ..types import Point, Graph
from ..models import GraphState

def drawer_content(label: str) -> rx.Component:
    return rx.drawer.content(
        rx.flex(
            rx.drawer.title(f"Details of {label}"),
            rx.button("Delete", width="100%", on_click=lambda: GraphState.Delete(label)),
            rx.button("Add Transformer", width="100%", on_click=lambda: GraphState.Append(label)),
            rx.drawer.close(rx.button("Close", width="100%")),
            align_items="start",
            direction="column",
            gap="1em",
        ),
        top="auto",
        right="auto",
        height="100%",
        width="20em",
        padding="2em",
        background_color="green",
    )

def plot_layout() -> rx.Component:
    return rx.box(
        rx.foreach(
            GraphState.GetPoints,
            lambda point: button_box_drawer(point, drawer_content)
        ),
        position="absolute",
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )