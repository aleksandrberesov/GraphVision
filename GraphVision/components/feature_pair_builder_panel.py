"""
Feature Pair Builder dialog.

Visual builder for GLMFeaturePairTransformation. Assign columns to a First and
a Second group; the result is the cartesian product of the two. A column placed
in one group is locked out of the other (groups must not overlap).
"""

import reflex as rx

from ..models.feature_pair_builder_state import FeaturePairBuilderState as S


def _first_badge(col: str) -> rx.Component:
    in_first = S.first_group.contains(col)  # type: ignore[attr-defined]
    in_second = S.second_group.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=S.toggle_first(col),
        cursor=rx.cond(in_second, "not-allowed", "pointer"),  # type: ignore[arg-type]
        color_scheme=rx.cond(  # type: ignore[arg-type]
            in_first, "green", rx.cond(in_second, "gray", "gray")  # type: ignore[arg-type]
        ),
        variant=rx.cond(  # type: ignore[arg-type]
            in_first, "solid", rx.cond(in_second, "soft", "outline")  # type: ignore[arg-type]
        ),
        opacity=rx.cond(in_second, "0.45", "1"),
        font_size="xs",
    )


def _second_badge(col: str) -> rx.Component:
    in_first = S.first_group.contains(col)  # type: ignore[attr-defined]
    in_second = S.second_group.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=S.toggle_second(col),
        cursor=rx.cond(in_first, "not-allowed", "pointer"),  # type: ignore[arg-type]
        color_scheme=rx.cond(  # type: ignore[arg-type]
            in_second, "green", rx.cond(in_first, "gray", "gray")  # type: ignore[arg-type]
        ),
        variant=rx.cond(  # type: ignore[arg-type]
            in_second, "solid", rx.cond(in_first, "soft", "outline")  # type: ignore[arg-type]
        ),
        opacity=rx.cond(in_first, "0.45", "1"),
        font_size="xs",
    )


def _group_row(label: str, badge_fn) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="xs", font_weight="bold", color="#111827"),
        rx.flex(
            rx.foreach(S.available_columns, badge_fn),
            flex_wrap="wrap",
            gap="1",
            width="100%",
        ),
        spacing="1",
        width="100%",
        align_items="flex_start",
    )


def _task_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.text(row["label"], flex="1", color="#374151", font_size="xs",
                overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.icon("x", size=14, color="#F87171", cursor="pointer",
                on_click=S.remove_task(row["idx"].to(int))),  # type: ignore[attr-defined]
        width="100%", align="center", spacing="2",
    )


def feature_pair_builder_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("git-merge", size=16, color="#2563EB"),
                    rx.text("Feature Pair Builder", color="#111827"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                rx.text(
                    "Assign columns to two groups — the result is every First × Second combination. "
                    "A column used in one group is locked out of the other.",
                    font_size="xs",
                    color="#6B7280",
                ),

                rx.cond(
                    S.available_columns,
                    rx.vstack(
                        _group_row("First group", _first_badge),
                        rx.divider(color="#E5E7EB"),
                        _group_row("Second group", _second_badge),
                        rx.hstack(
                            rx.text(
                                "Pairs to create: ",
                                font_size="xs",
                                color="#6B7280",
                            ),
                            rx.text(
                                S.pair_count,
                                font_size="xs",
                                font_weight="bold",
                                color="#111827",
                            ),
                            rx.spacer(),
                            rx.button(
                                "Clear",
                                on_click=S.clear_groups,
                                size="1",
                                variant="ghost",
                                color_scheme="gray",
                            ),
                            width="100%",
                            align="center",
                        ),
                        spacing="3",
                        width="100%",
                        align_items="flex_start",
                    ),
                    rx.text(
                        "No categorical columns available — apply the parent node first.",
                        font_size="xs",
                        color="#F87171",
                    ),
                ),

                # ── accumulate (add-mode only): stack multiple group-pairs, each
                #    becomes its own chained FeaturePair node on Apply ──
                rx.cond(
                    ~S.is_edit_mode,  # type: ignore[operator]
                    rx.vstack(
                        rx.button(
                            rx.hstack(rx.icon("plus", size=14), rx.text("Add pair"), spacing="1", align="center"),
                            on_click=S.add_task,
                            size="2",
                            variant="soft",
                            color_scheme="blue",
                        ),
                        rx.cond(
                            S.tasks,
                            rx.vstack(
                                rx.hstack(
                                    rx.text("Pairs (one node each):", font_size="xs",
                                            font_weight="bold", color="#111827"),
                                    rx.spacer(),
                                    rx.button("Clear all", on_click=S.clear_tasks, size="1",
                                              variant="ghost", color_scheme="red"),
                                    width="100%", align="center",
                                ),
                                rx.box(
                                    rx.vstack(rx.foreach(S.task_rows, _task_row), spacing="1", width="100%"),
                                    max_height="140px", overflow_y="auto", width="100%",
                                ),
                                spacing="1", width="100%", align_items="flex_start",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2", width="100%", align_items="flex_start",
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
                        rx.cond(S.is_edit_mode, "Save", "Apply"),
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
