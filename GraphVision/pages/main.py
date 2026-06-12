import reflex as rx

from ..components import (
    plot_layout,
    control_panel,
    top_menu,
    schema_panel,
    schema_constructor_panel,
    tiny_schema_panel,
    mapping_builder_panel,
    math_builder_panel,
    column_picker_panel,
    date_difference_builder_panel,
    feature_pair_builder_panel,
    cyclic_builder_panel,
    binning_builder_panel,
    target_builder_panel,
    numeric_to_categorical_builder_panel,
    logger_panel,
    model_config_panel,
)
from ..models import GraphState as State
from ..models.busy_state import BusyState


def main_page() -> rx.Component:
    return rx.vstack(
        rx.toast.provider(),
        top_menu(),
        rx.flex(
            rx.box(
                control_panel(),
                width="30%",
                height="100%",
                overflow_y="auto",
            ),
            rx.box(
                plot_layout(),
                width="70%",
                height="100%",
            ),
            width="100%",
            flex="1",
            spacing="0",
            bg="white",
            overflow="hidden",
        ),
        schema_panel(),
        schema_constructor_panel(),
        tiny_schema_panel(),
        mapping_builder_panel(),
        math_builder_panel(),
        column_picker_panel(),
        date_difference_builder_panel(),
        feature_pair_builder_panel(),
        cyclic_builder_panel(),
        binning_builder_panel(),
        target_builder_panel(),
        numeric_to_categorical_builder_panel(),
        model_config_panel(),
        logger_panel(),
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
