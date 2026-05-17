from typing import Any, Dict

import reflex as rx

from ..models.config_state import ConfigState


def _make_column_badges(param_name_var, param_value_var) -> rx.Component:
    """Render clickable column badges for a single list param.

    Uses a closure so both param_name_var and param_value_var (Vars from the
    outer rx.foreach) are captured and compiled into the inner foreach correctly.
    """
    def _badge(col: str) -> rx.Component:
        is_selected = param_value_var.to(str).contains(col)
        return rx.badge(
            col,
            on_click=ConfigState.toggle_column(param_name_var, col),
            cursor="pointer",
            color_scheme=rx.cond(is_selected, "green", "gray"), # type: ignore[arg-type]
            variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
            font_size="xs",
        )

    return rx.cond(
        ConfigState.available_columns,
        rx.vstack(
            rx.text("Select columns:", font_size="xs", color="#cccccc"),
            rx.flex(
                rx.foreach(ConfigState.available_columns, _badge),
                flex_wrap="wrap",
                gap="1",
                width="100%",
            ),
            spacing="1",
            width="100%",
        ),
        rx.fragment(),
    )


def _list_param_input(param: Dict[str, Any]) -> rx.Component:
    """Column picker: clickable badges from available_columns + a manual text input."""
    return rx.vstack(
        _make_column_badges(param["name"], param["value"]),
        rx.input(
            placeholder="col1, col2, ...",
            value=param["value"],
            on_change=ConfigState.update_param(param["name"]),
            width="100%",
            color="#111111",
            background_color="white",
            class_name="modal-input",
        ),
        spacing="1",
        width="100%",
    )


def _param_input(param: Dict[str, Any]) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(param["name"], font_size="xs", font_weight="bold", color="white"),
            rx.cond(
                param["required"],
                rx.text("*", color="#ff6b6b", font_size="xs"),
                rx.text("optional", color="#aaaaaa", font_size="xs"),
            ),
            spacing="1",
        ),
        rx.cond(
            param["is_list"],
            _list_param_input(param),
            rx.cond(
                param["is_bool"],
                rx.select(
                    ["true", "false"],
                    value=param["value"],
                    on_change=ConfigState.update_param(param["name"]),
                    width="100%",
                    color="#111111",
                    background_color="white",
                ),
                rx.input(
                    value=param["value"],
                    placeholder=rx.cond(param["required"], "required", "optional"),
                    on_change=ConfigState.update_param(param["name"]),
                    width="100%",
                    color="#111111",
                    background_color="white",
                    class_name="modal-input",
                ),
            ),
        ),
        spacing="1",
        width="100%",
        align_items="flex_start",
    )


_MODAL_INPUT_PLACEHOLDER_CSS = """
.modal-input::placeholder,
.modal-input input::placeholder {
    color: #0066cc !important;
    opacity: 1 !important;
}
"""


def config_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.el.style(_MODAL_INPUT_PLACEHOLDER_CSS),
            rx.dialog.title("Configure transformer"),
            rx.vstack(
                rx.select(
                    ConfigState.transformer_names,
                    placeholder="Select transformer…",
                    value=ConfigState.selected_class,
                    on_change=ConfigState.select_class,
                    width="100%",
                    color="#111111",
                    background_color="white",
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
                        rx.cond(ConfigState.is_edit_mode, "Save", "Add"),
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
    )
