from __future__ import annotations

import reflex as rx

from ..models.filter_state import FilterState
from ..models.plot_state import PlotState


def _cat_filter(col_meta: rx.Var) -> rx.Component:
    col = col_meta.col
    return rx.vstack(
        rx.text(col, font_size="xs", font_weight="500", color="#374151"),
        rx.vstack(
            rx.foreach(
                col_meta.top_values,
                lambda val: rx.hstack(
                    rx.checkbox(
                        checked=FilterState.checked_cat_keys.contains(col + "__" + val),
                        on_change=FilterState.toggle_cat_key(col + "__" + val),
                        size="1",
                    ),
                    rx.text(val, font_size="xs"),
                    spacing="1",
                    align_items="center",
                ),
            ),
            spacing="1",
            max_height="120px",
            overflow_y="auto",
        ),
        spacing="1",
        width="100%",
    )


def _num_filter(col_meta: rx.Var) -> rx.Component:
    col = col_meta.col
    return rx.vstack(
        rx.text(col, font_size="xs", font_weight="500", color="#374151"),
        rx.hstack(
            rx.input(
                placeholder="min",
                value=FilterState.num_lo[col],
                on_change=FilterState.set_num_lo(col),
                size="1",
                width="90px",
                font_size="xs",
            ),
            rx.text("–", font_size="xs", color="gray"),
            rx.input(
                placeholder="max",
                value=FilterState.num_hi[col],
                on_change=FilterState.set_num_hi(col),
                size="1",
                width="90px",
                font_size="xs",
            ),
            spacing="1",
            align_items="center",
        ),
        spacing="1",
        width="100%",
    )


def _col_filter(col_meta: rx.Var) -> rx.Component:
    return rx.cond(
        col_meta.type == "categorical",
        _cat_filter(col_meta),
        _num_filter(col_meta),
    )


def filter_panel() -> rx.Component:
    return rx.cond(
        FilterState.filter_columns,
        rx.vstack(
            # Header row: toggle button + "Filtered" badge
            rx.hstack(
                rx.button(
                    rx.cond(
                        FilterState.is_open,
                        rx.text("▲ Filters"),
                        rx.hstack(
                            rx.text("▼ Filters"),
                            rx.cond(
                                FilterState.is_filter_active,
                                rx.badge(
                                    FilterState.active_filter_count.to_string(),
                                    color_scheme="blue",
                                    size="1",
                                ),
                            ),
                            spacing="1",
                            align_items="center",
                        ),
                    ),
                    on_click=FilterState.toggle_open,
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                ),
                rx.spacer(),
                rx.cond(
                    FilterState.is_filter_active,
                    rx.text("filtered", font_size="xs", color="#2563eb", font_style="italic"),
                ),
                width="100%",
                align_items="center",
            ),
            # Collapsible body
            rx.cond(
                FilterState.is_open,
                rx.vstack(
                    rx.foreach(FilterState.filter_columns, _col_filter),
                    rx.hstack(
                        rx.button(
                            "Apply",
                            on_click=PlotState.reload_with_filter,
                            size="1",
                            variant="soft",
                            color_scheme="blue",
                        ),
                        rx.button(
                            "Clear",
                            on_click=[FilterState.clear_filters, PlotState.reload_with_filter],
                            size="1",
                            variant="ghost",
                            color_scheme="gray",
                        ),
                        spacing="2",
                    ),
                    spacing="3",
                    width="100%",
                    padding="8px",
                    border="1px solid #e5e7eb",
                    border_radius="6px",
                    background="#fafafa",
                ),
            ),
            width="100%",
            spacing="1",
        ),
    )
