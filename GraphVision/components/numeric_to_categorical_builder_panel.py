"""Numeric → Categorical Builder dialog (ordered vs unordered groups)."""

import reflex as rx

from ..models.numeric_to_categorical_builder_state import NumericToCategoricalBuilderState as S


def _ordered_badge(col: str) -> rx.Component:
    in_ordered = S.ordered_features.contains(col)  # type: ignore[attr-defined]
    in_unordered = S.unordered_features.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=S.toggle_ordered(col),
        cursor=rx.cond(in_unordered, "not-allowed", "pointer"),  # type: ignore[arg-type]
        color_scheme=rx.cond(in_ordered, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(  # type: ignore[arg-type]
            in_ordered, "solid", rx.cond(in_unordered, "soft", "outline")  # type: ignore[arg-type]
        ),
        opacity=rx.cond(in_unordered, "0.45", "1"),
        font_size="xs",
    )


def _unordered_badge(col: str) -> rx.Component:
    in_ordered = S.ordered_features.contains(col)  # type: ignore[attr-defined]
    in_unordered = S.unordered_features.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=S.toggle_unordered(col),
        cursor=rx.cond(in_ordered, "not-allowed", "pointer"),  # type: ignore[arg-type]
        color_scheme=rx.cond(in_unordered, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(  # type: ignore[arg-type]
            in_unordered, "solid", rx.cond(in_ordered, "soft", "outline")  # type: ignore[arg-type]
        ),
        opacity=rx.cond(in_ordered, "0.45", "1"),
        font_size="xs",
    )


def _group_row(label: str, hint: str, badge_fn, on_all, on_invert) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(label, font_size="xs", font_weight="bold", color="#111827"),
            rx.text(hint, font_size="xs", color="#9CA3AF"),
            rx.spacer(),
            rx.button("All", on_click=on_all, size="1", variant="ghost", color_scheme="blue"),
            rx.button("Invert", on_click=on_invert, size="1", variant="ghost", color_scheme="blue"),
            spacing="2", align="center", width="100%",
        ),
        rx.flex(
            rx.foreach(S.available_columns, badge_fn),
            flex_wrap="wrap", gap="1", width="100%",
        ),
        spacing="1", width="100%", align_items="flex_start",
    )


def numeric_to_categorical_builder_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("layers", size=16, color="#2563EB"),
                    rx.text("Numeric → Categorical Builder", color="#111827"),
                    spacing="2", align="center",
                ),
            ),
            rx.vstack(
                rx.text(
                    "Assign numeric columns to encode as ordered or unordered categories. "
                    "A column in one group is locked out of the other.",
                    font_size="xs", color="#6B7280",
                ),
                rx.cond(
                    S.available_columns,
                    rx.vstack(
                        _group_row(
                            "Ordered", "(ranked categories)", _ordered_badge,
                            S.select_all_ordered, S.invert_ordered,
                        ),
                        rx.divider(color="#E5E7EB"),
                        _group_row(
                            "Unordered", "(nominal categories)", _unordered_badge,
                            S.select_all_unordered, S.invert_unordered,
                        ),
                        rx.hstack(
                            rx.spacer(),
                            rx.button("Clear", on_click=S.clear_groups, size="1",
                                      variant="ghost", color_scheme="gray"),
                            width="100%",
                        ),
                        spacing="3", width="100%", align_items="flex_start",
                    ),
                    rx.text("No numeric columns available — apply the parent node first.",
                            font_size="xs", color="#F87171"),
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
