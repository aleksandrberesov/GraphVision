import reflex as rx
from ..models import GraphState as State

def control_panel() -> rx.Component:
    return rx.vstack(
        rx.divider(orientation="horizontal", size="4", color_scheme="blue"),
        rx.vstack(
            rx.button(
                "Clear graph",
                on_click=State.clear_graph,
                width="100%",
            ),
            rx.button(
                "Add node",
                on_click=State.add_node,
                width="100%",
            ),
            rx.button(
                "Delete selected node",
                on_click=State.delete_node(State.selected_node_id),
                width="100%",
            ),
            width="100%",
        ),
        rx.divider(orientation="horizontal", size="4", color_scheme="blue"),
        rx.vstack(
            rx.text("Selected Node Path:", font_size="md", font_weight="bold"),
            height="50%",
            width="100%",
            background_color="green",
        ),
        rx.divider(orientation="horizontal", size="4", color_scheme="blue"),
        rx.box(
            rx.text(State.selected_node_id, font_size="lg"),
            background_color="orange",
            width="40%",
        ),
        rx.box(
            rx.text(State.selected_edge_id, font_size="lg"),
            background_color="orange",
            width="40%",
        ),
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
        spacing="4",
    )