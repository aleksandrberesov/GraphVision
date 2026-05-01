import reflex as rx

from ..models.config_state import ConfigState
from ..models import GraphState


def _palette_button(class_name: str) -> rx.Component:
    return rx.tooltip(
        rx.button(
            class_name[:3],
            on_click=ConfigState.open_dialog_with_class(class_name),
            disabled=GraphState.selected_node_id == "",
            width="46px",
            height="30px",
            padding="0",
            font_size="10px",
            variant="outline",
            color_scheme="blue",
        ),
        content=class_name,
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
            rx.foreach(ConfigState.transformer_names, _palette_button),
            flex_wrap="wrap",
            gap="2",
            width="100%",
        ),
        on_mount=ConfigState.load_transformers,
        width="100%",
        padding_y="2",
    )
