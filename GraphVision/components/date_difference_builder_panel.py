"""
Date Difference Builder dialog.

Visual builder for GLMDateDifferenceTransformation's ``differences`` param.
Pick a difference type and a From/To column pair, "+ Add" to stack it; repeat.
"""

from typing import Dict

import reflex as rx

from ..models.date_difference_builder_state import DateDifferenceBuilderState as S


def _entry_row(row: Dict[str, str]) -> rx.Component:
    return rx.hstack(
        rx.text(
            row["label"],
            width="55%",
            color="#111827",
            font_size="sm",
            font_weight="bold",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.text(row["features"], flex="1", color="#374151", font_size="xs"),
        rx.icon(
            "x",
            size=14,
            color="#F87171",
            cursor="pointer",
            on_click=S.remove_entry(row["name"]),
        ),
        width="100%",
        align="center",
        spacing="2",
    )


def _from_badge(col: str) -> rx.Component:
    is_selected = S.from_cols.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=S.toggle_from(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
        font_size="xs",
    )


def _to_badge(col: str) -> rx.Component:
    is_selected = S.to_cols.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=S.toggle_to(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
        font_size="xs",
    )


def date_difference_builder_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("calendar-minus", size=16, color="#2563EB"),
                    rx.text("Date Difference Builder", color="#111827"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                rx.text(
                    "Tick type(s), pick From and To columns (or a fixed date), then “+ Add”.",
                    font_size="xs",
                    color="#6B7280",
                ),

                # ── difference types (multi) ─────────────────────────────
                rx.vstack(
                    rx.text("Types", font_size="xs", font_weight="bold", color="#111827"),
                    rx.flex(
                        rx.checkbox("days", checked=S.use_days, on_change=S.set_use_days, color_scheme="blue"),
                        rx.checkbox("months", checked=S.use_months, on_change=S.set_use_months, color_scheme="blue"),
                        rx.checkbox("years", checked=S.use_years, on_change=S.set_use_years, color_scheme="blue"),
                        gap="3", flex_wrap="wrap", width="100%",
                    ),
                    spacing="1", width="100%", align_items="flex_start",
                ),

                # ── FROM columns (multi) ─────────────────────────────────
                rx.vstack(
                    rx.text("From", font_size="xs", font_weight="bold", color="#111827"),
                    rx.flex(rx.foreach(S.available_columns, _from_badge),
                            flex_wrap="wrap", gap="1", width="100%"),
                    spacing="1", width="100%", align_items="flex_start",
                ),

                # ── TO columns (multi) or a fixed date ───────────────────
                rx.vstack(
                    rx.hstack(
                        rx.text("To", font_size="xs", font_weight="bold", color="#111827"),
                        rx.checkbox(
                            "fixed date",
                            checked=S.to_is_fixed,
                            on_change=S.set_to_is_fixed,
                            size="1",
                            color_scheme="blue",
                        ),
                        spacing="2", align="center",
                    ),
                    rx.cond(
                        S.to_is_fixed,
                        rx.input(
                            value=S.to_fixed_value,
                            on_change=S.set_to_fixed_value,
                            placeholder="2025-01",
                            color="#111111",
                            background_color="white",
                            width="180px",
                        ),
                        rx.flex(rx.foreach(S.available_columns, _to_badge),
                                flex_wrap="wrap", gap="1", width="100%"),
                    ),
                    spacing="1", width="100%", align_items="flex_start",
                ),

                rx.button(
                    rx.hstack(rx.icon("plus", size=14), rx.text("Add"), spacing="1", align="center"),
                    on_click=S.add_current,
                    size="2",
                    color_scheme="blue",
                    variant="soft",
                ),

                rx.cond(
                    S.entries,
                    rx.vstack(
                        rx.divider(color="#E5E7EB"),
                        rx.hstack(
                            rx.text(
                                "Differences:",
                                font_size="xs",
                                font_weight="bold",
                                color="#111827",
                            ),
                            rx.spacer(),
                            rx.button(
                                "Clear all",
                                on_click=S.clear_entries,
                                size="1",
                                variant="ghost",
                                color_scheme="red",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.foreach(S.entry_rows, _entry_row),
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

                rx.hstack(
                    rx.button(
                        "Cancel",
                        on_click=S.close,
                        variant="outline",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.cond(S.is_edit_mode, "Save", "Add"),
                        on_click=S.submit,
                        disabled=~S.can_submit,  # type: ignore[operator]
                        color_scheme="blue",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="600px",
        ),
        open=S.is_open,
        on_open_change=S.set_is_open,
    )
