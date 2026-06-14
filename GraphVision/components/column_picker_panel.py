"""
Shared "pick columns" builder dialog.

Drives both GLMDateTransformation (pick date columns) and
GLMColumnRemoverTransformation (pick columns to keep — the complement is
removed). All transformer-specific text/behaviour lives in ColumnPickerState.
"""

import reflex as rx

from ..models.column_picker_state import ColumnPickerState


def _column_badge(col: str) -> rx.Component:
    is_selected = ColumnPickerState.selected_columns.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=ColumnPickerState.toggle_column(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
        font_size="xs",
    )


def _removed_badge(col: str) -> rx.Component:
    return rx.badge(col, color_scheme="red", variant="soft", font_size="xs")


def column_picker_panel() -> rx.Component:
    """Shared single-multiselect column picker dialog (rendered once)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon(ColumnPickerState.icon, size=16, color="#2563EB"),
                    rx.text(ColumnPickerState.title, color="#111827"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                rx.text(ColumnPickerState.hint, font_size="xs", color="#6B7280"),

                rx.hstack(
                    rx.button(
                        "Select all",
                        on_click=ColumnPickerState.select_all,
                        size="1",
                        variant="ghost",
                        color_scheme="blue",
                    ),
                    rx.button(
                        "Invert",
                        on_click=ColumnPickerState.invert,
                        size="1",
                        variant="ghost",
                        color_scheme="blue",
                    ),
                    rx.button(
                        "Clear",
                        on_click=ColumnPickerState.clear_all,
                        size="1",
                        variant="ghost",
                        color_scheme="gray",
                    ),
                    spacing="2",
                ),

                rx.cond(
                    ColumnPickerState.available_columns,
                    rx.box(
                        rx.flex(
                            rx.foreach(ColumnPickerState.available_columns, _column_badge),
                            flex_wrap="wrap",
                            gap="1",
                            width="100%",
                        ),
                        max_height="240px",
                        overflow_y="auto",
                        width="100%",
                    ),
                    rx.text(
                        "No columns available — apply the parent node first.",
                        font_size="xs",
                        color="#F87171",
                    ),
                ),

                # For ColumnRemover: show what will be dropped.
                rx.cond(
                    ColumnPickerState.removed_preview,
                    rx.vstack(
                        rx.divider(color="#E5E7EB"),
                        rx.text(
                            "Will be removed:",
                            font_size="xs",
                            font_weight="bold",
                            color="#111827",
                        ),
                        rx.flex(
                            rx.foreach(ColumnPickerState.removed_preview, _removed_badge),
                            flex_wrap="wrap",
                            gap="1",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                        align_items="flex_start",
                    ),
                    rx.fragment(),
                ),

                # ColumnRemover: multicollinearity of the kept columns.
                rx.cond(
                    ColumnPickerState.mode == "remove_complement",
                    rx.hstack(
                        rx.button(
                            "Recompute stability",
                            on_click=ColumnPickerState.recompute_stability,
                            size="1",
                            variant="soft",
                            color_scheme="blue",
                        ),
                        rx.text("Stability:", font_size="xs", color="#6B7280"),
                        rx.text(
                            ColumnPickerState.stability_text,
                            font_size="xs",
                            font_weight="bold",
                            color="#111827",
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    rx.fragment(),
                ),

                rx.divider(color="#E5E7EB"),

                rx.hstack(
                    rx.button(
                        "Cancel",
                        on_click=ColumnPickerState.close,
                        variant="outline",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.cond(ColumnPickerState.is_edit_mode, "Save", "Add"),
                        on_click=ColumnPickerState.submit,
                        disabled=~ColumnPickerState.can_submit,  # type: ignore[operator]
                        color_scheme="blue",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="560px",
        ),
        open=ColumnPickerState.is_open,
        on_open_change=ColumnPickerState.set_is_open,
    )
