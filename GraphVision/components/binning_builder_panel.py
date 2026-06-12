"""Binning Builder dialog (method + n_bins per column)."""

from typing import Dict

import reflex as rx

from ..models.binning_builder_state import BinningBuilderState as S


def _column_badge(col: str) -> rx.Component:
    is_selected = S.selected_features.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=S.toggle_feature(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
        font_size="xs",
    )


def _entry_row(row: Dict[str, str]) -> rx.Component:
    return rx.hstack(
        rx.text(row["col"], width="40%", color="#111827", font_size="sm", font_weight="bold",
                overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.text(row["summary"], flex="1", color="#374151", font_size="xs"),
        rx.icon("x", size=14, color="#F87171", cursor="pointer", on_click=S.remove_entry(row["col"])),
        width="100%", align="center", spacing="2",
    )


def binning_builder_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("bar-chart-2", size=16, color="#2563EB"),
                    rx.text("Binning Builder", color="#111827"),
                    spacing="2", align="center",
                ),
            ),
            rx.vstack(
                rx.text("Pick a method & n_bins, select columns, then “+ Add”.", font_size="xs", color="#6B7280"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Method", font_size="xs", color="#111827"),
                        rx.select(
                            S.method_labels,
                            value=S.method_label,
                            on_change=S.set_method,
                            color="#111111", background_color="white", width="240px",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("n_bins", font_size="xs", color="#111827"),
                        rx.input(value=S.n_bins, on_change=S.set_n_bins, placeholder="5",
                                 width="90px", color="#111111", background_color="white"),
                        spacing="1",
                    ),
                    spacing="3", align="end",
                ),
                rx.vstack(
                    rx.text("Columns:", font_size="xs", font_weight="bold", color="#111827"),
                    rx.cond(
                        S.available_columns,
                        rx.flex(rx.foreach(S.available_columns, _column_badge),
                                flex_wrap="wrap", gap="1", width="100%"),
                        rx.text("No numeric columns available — apply the parent node first.",
                                font_size="xs", color="#F87171"),
                    ),
                    spacing="1", width="100%", align_items="flex_start",
                ),
                rx.button(
                    rx.hstack(rx.icon("plus", size=14), rx.text("Add"), spacing="1", align="center"),
                    on_click=S.add_current, size="2", color_scheme="blue", variant="soft",
                ),
                rx.cond(
                    S.entries,
                    rx.vstack(
                        rx.divider(color="#E5E7EB"),
                        rx.hstack(
                            rx.text("Configured columns:", font_size="xs", font_weight="bold", color="#111827"),
                            rx.spacer(),
                            rx.button("Clear all", on_click=S.clear_entries, size="1", variant="ghost", color_scheme="red"),
                            width="100%", align="center",
                        ),
                        rx.box(
                            rx.vstack(rx.foreach(S.entry_rows, _entry_row), spacing="1", width="100%"),
                            max_height="180px", overflow_y="auto", width="100%",
                        ),
                        spacing="2", width="100%", align_items="flex_start",
                    ),
                    rx.fragment(),
                ),
                rx.divider(color="#E5E7EB"),
                rx.hstack(
                    rx.button("Cancel", on_click=S.close, variant="outline", color_scheme="gray"),
                    rx.button(rx.cond(S.is_edit_mode, "Save", "Add"), on_click=S.submit,
                              disabled=~S.can_submit, color_scheme="blue"),  # type: ignore[operator]
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="600px",
        ),
        open=S.is_open,
        on_open_change=S.set_is_open,
    )
