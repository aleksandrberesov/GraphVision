import reflex as rx

from ..models.config_state import ConfigState
from ..models import GraphState


def _palette_button(entry: dict) -> rx.Component:
    is_tiny = entry["name"] == "GLMTinySchemaTransformation"
    return rx.tooltip(
        rx.button(
            rx.icon(entry["icon"], size=15),
            on_click=ConfigState.open_dialog_with_class(entry["name"]),
            # Disabled with no node selected, and — when the selected node is the
            # root — for every transformer except Tiny Schema (must be Node 1).
            disabled=(GraphState.selected_node_id == "")
            | (GraphState.selected_is_root & ~is_tiny),
            width="34px",
            height="34px",
            padding="0",
            variant="outline",
            color_scheme="blue",
        ),
        content=entry["name"],
    )


def transformer_palette() -> rx.Component:
    return rx.box(
        rx.text(
            "Transformers",
            font_size="xs",
            font_weight="bold",
            color="gray",
            margin_bottom="2",
        ),
        rx.flex(
            rx.foreach(ConfigState.transformer_entries, _palette_button),
            flex_wrap="wrap",
            gap="2",
            width="100%",
        ),
        on_mount=ConfigState.load_transformers,
        width="100%",
        padding_y="2",
    )
