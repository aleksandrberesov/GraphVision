import reflex as rx
from ..models import GraphState as State
from ..models import NodeState as Node
from ..models.config_state import ConfigState
from ..models.schema_state import SchemaState
from .config_panel import config_panel
from .results_panel import results_panel
from .upload_box import upload_box
from .transformer_palette import transformer_palette


def _vertex_properties() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Selected vertex",
            font_size="xs",
            font_weight="bold",
            color="gray",
        ),
        rx.cond(
            (Node.id == "None") | (Node.id == None),
            rx.text("No node selected", color="gray", font_size="xs"),
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Title:",
                        font_size="sm",
                        font_weight="bold",
                        color="black",
                        white_space="nowrap",
                    ),
                    rx.input(
                        value=Node.label,
                        on_change=Node.update_label,
                        placeholder="no title",
                        color="black",
                        flex="1",
                    ),
                    align="center",
                    width="100%",
                    spacing="2",
                ),
                rx.cond(
                    Node.is_root,
                    rx.button(
                        "Configure schema",
                        on_click=SchemaState.open_schema,
                        width="100%",
                        variant="soft",
                        color_scheme="blue",
                    ),
                    rx.button(
                        "Configure transformer",
                        on_click=ConfigState.open_edit_dialog,
                        width="100%",
                        variant="soft",
                    ),
                ),
                config_panel(),
                results_panel(),
                rx.button(
                    "Fit",
                    on_click=State.manifest_node(Node.id),
                    disabled=Node.is_fitted,
                    width="100%",
                    variant="soft",
                    color_scheme="blue",
                ),
                rx.button(
                    "Delete node",
                    on_click=State.delete_node(State.selected_node_id),
                    width="100%",
                    variant="outline",
                    color_scheme="red",
                ),
                rx.cond(
                    Node.errors,
                    rx.vstack(
                        rx.text("Errors:", color="red", font_size="sm", font_weight="bold"),
                        rx.foreach(
                            Node.errors,
                            lambda e: rx.text(e, color="red", font_size="xs"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                spacing="2",
            ),
        ),
        width="100%",
        border="1px solid #e5e7eb",
        border_radius="6px",
        padding="2",
        spacing="2",
    )


def control_panel() -> rx.Component:
    return rx.vstack(
        # ── Top: graph identity + graph-level actions ──
        rx.vstack(
            rx.input(
                value=State.title,
                placeholder="Graph name",
                on_change=State.set_name,
                width="100%",
            ),
            upload_box(),
            width="100%",
            spacing="2",
        ),
        rx.divider(orientation="horizontal", size="4", color_scheme="blue"),
        # ── Middle: transformer palette (always visible) ──
        transformer_palette(),
        rx.divider(orientation="horizontal", size="4", color_scheme="blue"),
        # ── Bottom: vertex properties (stable container) ──
        _vertex_properties(),
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
        spacing="3",
        padding="3",
        overflow_y="auto",
    )
