"""
GLM model node configuration dialog.

Lets the user pick a GLM family and a link function (link list updates
when family changes), then adds a model vertex to the graph.
"""

import reflex as rx

from ..models.model_config_state import ModelConfigState


def _family_select() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Family", font_size="xs", font_weight="bold", color="#111827"),
            rx.text("*", color="#ff6b6b", font_size="xs"),
            spacing="1",
        ),
        rx.select(
            ModelConfigState.family_names,
            value=ModelConfigState.selected_family,
            on_change=ModelConfigState.set_family,
            width="100%",
            color="#111111",
            background_color="white",
        ),
        spacing="1",
        width="100%",
        align_items="flex_start",
    )


def _link_select() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Link", font_size="xs", font_weight="bold", color="#111827"),
            rx.text("*", color="#ff6b6b", font_size="xs"),
            spacing="1",
        ),
        rx.select(
            ModelConfigState.available_links,
            value=ModelConfigState.selected_link,
            on_change=ModelConfigState.set_link,
            width="100%",
            color="#111111",
            background_color="white",
        ),
        rx.text(
            rx.text.span("Canonical: ", color="#6B7280", font_size="xs"),
            rx.text.span(ModelConfigState.canonical_link, color="#2563EB", font_size="xs"),
        ),
        spacing="1",
        width="100%",
        align_items="flex_start",
    )


def model_config_panel() -> rx.Component:
    """GLM model configuration dialog (rendered once in the page layout)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("cpu", size=16, color="#7C3AED"),
                    rx.text("Add GLM Model Node", color="#111827"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                # Info banner
                rx.box(
                    rx.text(
                        "The model node fits a statsmodels GLM on the branch's data. "
                        "After adding, select the node and click 'Apply' to fit.",
                        font_size="xs",
                        color="#6B7280",
                    ),
                    padding="2",
                    border_radius="4px",
                    background="#F3F4F6",
                    width="100%",
                ),

                _family_select(),
                _link_select(),

                # Action buttons
                rx.hstack(
                    rx.button(
                        "Cancel",
                        on_click=ModelConfigState.close,
                        variant="outline",
                        color_scheme="gray",
                    ),
                    rx.button(
                        "Add model",
                        on_click=ModelConfigState.apply,
                        disabled=~ModelConfigState.can_apply,  # type: ignore[operator]
                        color_scheme="violet",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="420px",
        ),
        open=ModelConfigState.is_open,
        on_open_change=ModelConfigState.set_is_open,
    )
