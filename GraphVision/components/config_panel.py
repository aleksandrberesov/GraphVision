from typing import Any, Dict, List

import reflex as rx

from ..models.config_state import ConfigState


def _make_column_badges(param_name_var, param_value_var) -> rx.Component:
    """Render clickable column badges for a single list param.

    Uses a closure so both param_name_var and param_value_var (Vars from the
    outer rx.foreach) are captured and compiled into the inner foreach correctly.
    """
    def _badge(col: str) -> rx.Component:
        # Exact membership against the tokenised value — NOT a substring test,
        # which used to make "YearMonth" light up when only "YearMonth_year" was
        # selected. The value is always joined with ", " (see toggle_column).
        is_selected = param_value_var.to(str).split(", ").contains(col)
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
            rx.text("Select columns:", font_size="xs", color="#111827"),
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


def _make_fixed_choice_badges(param_name_var, param_value_var, choices_var) -> rx.Component:
    """Render clickable badges for a fixed set of choices (e.g. aggregation options)."""
    def _badge(choice: str) -> rx.Component:
        # Exact membership against the tokenised value (see _make_column_badges).
        is_selected = param_value_var.to(str).split(", ").contains(choice)
        return rx.badge(
            choice,
            on_click=ConfigState.toggle_column(param_name_var, choice),
            cursor="pointer",
            color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
            variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
            font_size="xs",
        )

    return rx.vstack(
        rx.text("Select values:", font_size="xs", color="#111827"),
        rx.flex(
            rx.foreach(choices_var.to(List[str]), _badge),
            flex_wrap="wrap",
            gap="1",
            width="100%",
        ),
        spacing="1",
        width="100%",
    )


def _list_param_input(param: Dict[str, Any]) -> rx.Component:
    """Column picker: fixed-choice or column badges + a manual text input."""
    return rx.vstack(
        rx.cond(
            param["list_choices"],
            _make_fixed_choice_badges(param["name"], param["value"], param["list_choices"]),
            _make_column_badges(param["name"], param["value"]),
        ),
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


def _dict_param_input(param: Dict[str, Any]) -> rx.Component:
    """JSON textarea for dict-type params."""
    return rx.text_area(
        value=param["value"],
        placeholder='{"key": "value"}',
        on_change=ConfigState.update_param(param["name"]),
        width="100%",
        min_height="80px",
        color="#111111",
        background_color="white",
        font_family="monospace",
        font_size="xs",
    )


def _param_input(param: Dict[str, Any]) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(param["name"], font_size="xs", font_weight="bold", color="#111827"),
            rx.cond(
                param["required"],
                rx.text("*", color="#ff6b6b", font_size="xs"),
                rx.text("optional", color="#6B7280", font_size="xs"),
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
                rx.cond(
                    param["is_enum"],
                    rx.select(
                        param["choices"].to(List[str]),
                        value=param["value"],
                        on_change=ConfigState.update_param(param["name"]),
                        width="100%",
                        color="#111111",
                        background_color="white",
                    ),
                    rx.cond(
                        param["is_dict"],
                        _dict_param_input(param),
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
            rx.dialog.title("Configure transformer", color="#111827"),
            rx.vstack(
                rx.select(
                    ConfigState.allowed_transformer_names,
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
                            color="#111827",
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
