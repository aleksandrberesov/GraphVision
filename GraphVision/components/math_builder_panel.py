"""
Mathematical Transform Builder dialog.

Visual builder for GLMMathematicalTransformation's nested ``transformations``
param. The user ticks transform types (log / double_log / exp / power-range /
power-list), fills any conditional fields, picks numeric columns, and clicks
"+ Add" to stack that transform onto every selected column. Accumulated
entries are shown below; "Add"/"Save" builds the full dict automatically.
"""

from typing import Dict

import reflex as rx

from ..models.math_builder_state import MathBuilderState


# ── transform-type checkboxes ────────────────────────────────────────────────

def _type_checkboxes() -> rx.Component:
    return rx.flex(
        rx.checkbox(
            "log",
            checked=MathBuilderState.use_log,
            on_change=MathBuilderState.set_use_log,
            color_scheme="blue",
        ),
        rx.checkbox(
            "double_log",
            checked=MathBuilderState.use_double_log,
            on_change=MathBuilderState.set_use_double_log,
            color_scheme="blue",
        ),
        rx.checkbox(
            "exp",
            checked=MathBuilderState.use_exp,
            on_change=MathBuilderState.set_use_exp,
            color_scheme="blue",
        ),
        rx.checkbox(
            "power_range",
            checked=MathBuilderState.use_power_range,
            on_change=MathBuilderState.set_use_power_range,
            color_scheme="blue",
        ),
        rx.checkbox(
            "power_list",
            checked=MathBuilderState.use_power_list,
            on_change=MathBuilderState.set_use_power_list,
            color_scheme="blue",
        ),
        flex_wrap="wrap",
        gap="3",
        width="100%",
    )


def _conditional_fields() -> rx.Component:
    return rx.fragment(
        rx.cond(
            MathBuilderState.use_power_range,
            rx.hstack(
                rx.text("From:", font_size="xs", color="#111827"),
                rx.input(
                    value=MathBuilderState.pr_from,
                    on_change=MathBuilderState.set_pr_from,
                    placeholder="-1",
                    size="1",
                    width="80px",
                    color="#111111",
                    background_color="white",
                ),
                rx.text("To:", font_size="xs", color="#111827"),
                rx.input(
                    value=MathBuilderState.pr_to,
                    on_change=MathBuilderState.set_pr_to,
                    placeholder="3",
                    size="1",
                    width="80px",
                    color="#111111",
                    background_color="white",
                ),
                spacing="2",
                align="center",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MathBuilderState.use_power_list,
            rx.hstack(
                rx.text("Powers:", font_size="xs", color="#111827"),
                rx.input(
                    value=MathBuilderState.pl_values,
                    on_change=MathBuilderState.set_pl_values,
                    placeholder="-1, 0.5, 2, 3",
                    size="1",
                    width="220px",
                    color="#111111",
                    background_color="white",
                ),
                spacing="2",
                align="center",
            ),
            rx.fragment(),
        ),
    )


# ── column picker ─────────────────────────────────────────────────────────────

def _column_badge(col: str) -> rx.Component:
    is_selected = MathBuilderState.selected_features.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=MathBuilderState.toggle_feature(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "surface"),  # type: ignore[arg-type]
        font_size="xs",
    )


# ── accumulated entry rows ────────────────────────────────────────────────────

def _entry_row(row: Dict[str, str]) -> rx.Component:
    return rx.hstack(
        rx.text(
            row["col"],
            width="40%",
            color="#111827",
            font_size="sm",
            font_weight="bold",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.text(
            row["summary"],
            flex="1",
            color="#374151",
            font_size="xs",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.icon(
            "x",
            size=14,
            color="#F87171",
            cursor="pointer",
            on_click=MathBuilderState.remove_entry(row["col"]),
        ),
        width="100%",
        align="center",
        spacing="2",
    )


# ── public component ──────────────────────────────────────────────────────────

def math_builder_panel() -> rx.Component:
    """Mathematical Transform Builder dialog (rendered once in the page layout)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("sigma", size=16, color="#2563EB"),
                    rx.text("Mathematical Transform Builder", color="#111827"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                rx.text(
                    "Tick transform type(s), fill any fields, pick columns, then “+ Add”.",
                    font_size="xs",
                    color="#6B7280",
                ),

                # ── transform types + conditional fields ─────────────────
                _type_checkboxes(),
                _conditional_fields(),

                rx.divider(color="#E5E7EB"),

                # ── column picker ────────────────────────────────────────
                rx.vstack(
                    rx.text(
                        "Columns:",
                        font_size="xs",
                        font_weight="bold",
                        color="#111827",
                    ),
                    rx.cond(
                        MathBuilderState.available_columns,
                        rx.flex(
                            rx.foreach(MathBuilderState.available_columns, _column_badge),
                            flex_wrap="wrap",
                            gap="1",
                            width="100%",
                        ),
                        rx.text(
                            "No numeric columns available — apply the parent node first.",
                            font_size="xs",
                            color="#F87171",
                        ),
                    ),
                    spacing="1",
                    width="100%",
                    align_items="flex_start",
                ),

                rx.button(
                    rx.hstack(rx.icon("plus", size=14), rx.text("Add"), spacing="1", align="center"),
                    on_click=MathBuilderState.add_current,
                    size="2",
                    color_scheme="blue",
                    variant="soft",
                ),

                # ── accumulated entries ──────────────────────────────────
                rx.cond(
                    MathBuilderState.entries,
                    rx.vstack(
                        rx.divider(color="#E5E7EB"),
                        rx.hstack(
                            rx.text(
                                "Configured columns:",
                                font_size="xs",
                                font_weight="bold",
                                color="#111827",
                            ),
                            rx.spacer(),
                            rx.button(
                                "Clear all",
                                on_click=MathBuilderState.clear_entries,
                                size="1",
                                variant="ghost",
                                color_scheme="red",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.foreach(MathBuilderState.entry_rows, _entry_row),
                                spacing="1",
                                width="100%",
                            ),
                            max_height="180px",
                            overflow_y="auto",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="flex_start",
                    ),
                    rx.fragment(),
                ),

                rx.divider(color="#E5E7EB"),

                # ── action buttons ───────────────────────────────────────
                rx.hstack(
                    rx.button(
                        "Cancel",
                        on_click=MathBuilderState.close,
                        variant="soft",
                        color_scheme="brown",
                    ),
                    rx.button(
                        rx.cond(MathBuilderState.is_edit_mode, "Save", "Add"),
                        on_click=MathBuilderState.submit,
                        disabled=~MathBuilderState.can_submit,  # type: ignore[operator]
                        color_scheme="blue",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            background_color="white",
            max_width="560px",
        ),
        open=MathBuilderState.is_open,
        on_open_change=MathBuilderState.set_is_open,
    )
