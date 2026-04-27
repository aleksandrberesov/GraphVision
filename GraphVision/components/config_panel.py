from typing import Any, Dict

import reflex as rx

from ..models.config_state import ConfigState


def _param_input(param: Dict[str, Any]) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(param["name"], font_size="xs", font_weight="bold", color="black"),
            rx.cond(
                param["required"],
                rx.text("*", color="red", font_size="xs"),
                rx.text("optional", color="gray", font_size="xs"),
            ),
            spacing="1",
        ),
        rx.cond(
            param["is_list"],
            rx.vstack(
                rx.cond(
                    ConfigState.available_columns,
                    rx.text(
                        "Available: " + ConfigState.available_columns_hint,
                        font_size="xs",
                        color="gray",
                        font_style="italic",
                    ),
                    rx.fragment(),
                ),
                rx.input(
                    placeholder="col1, col2, ...",
                    value=param["value"],
                    on_change=ConfigState.update_param(param["name"]),
                    width="100%",
                    color="black",
                ),
                spacing="1",
                width="100%",
            ),
            rx.cond(
                param["is_bool"],
                rx.select(
                    ["true", "false"],
                    value=param["value"],
                    on_change=ConfigState.update_param(param["name"]),
                    width="100%",
                ),
                rx.input(
                    value=param["value"],
                    placeholder=rx.cond(param["required"], "required", "optional"),
                    on_change=ConfigState.update_param(param["name"]),
                    width="100%",
                    color="black",
                ),
            ),
        ),
        spacing="1",
        width="100%",
        align_items="flex_start",
    )


def config_panel() -> rx.Component:
    return rx.fragment(
        rx.button(
            "Add transformation",
            on_click=ConfigState.open_dialog,
            width="100%",
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Add Transformation"),
                rx.vstack(
                    rx.select(
                        ConfigState.transformer_names,
                        placeholder="Select transformer…",
                        value=ConfigState.selected_class,
                        on_change=ConfigState.select_class,
                        width="100%",
                    ),
                    rx.cond(
                        ConfigState.param_schema,
                        rx.vstack(
                            rx.foreach(ConfigState.param_schema, _param_input),
                            width="100%",
                            spacing="3",
                            max_height="350px",
                            overflow_y="auto",
                        ),
                        rx.cond(
                            ConfigState.selected_class != "",
                            rx.text(
                                "No parameters required.",
                                color="gray",
                                font_size="sm",
                            ),
                            rx.fragment(),
                        ),
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            on_click=ConfigState.close_dialog,
                            variant="outline",
                            color_scheme="gray",
                        ),
                        rx.button(
                            "Add",
                            on_click=ConfigState.submit,
                            disabled=ConfigState.selected_class == "",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                max_width="480px",
            ),
            open=ConfigState.is_open,
            on_open_change=ConfigState.set_is_open,
        ),
    )
