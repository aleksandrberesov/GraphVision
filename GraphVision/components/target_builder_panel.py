"""Target Encoding Builder dialog (features + aggregations + one target)."""

import reflex as rx

from ..models.target_builder_state import TargetBuilderState as S


def _feature_badge(col: str) -> rx.Component:
    is_selected = S.selected_features.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=S.toggle_feature(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
        font_size="xs",
    )


def _agg_badge(agg: str) -> rx.Component:
    is_selected = S.selected_aggs.contains(agg)  # type: ignore[attr-defined]
    return rx.badge(
        agg,
        on_click=S.toggle_agg(agg),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
        font_size="xs",
    )


def target_builder_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("crosshair", size=16, color="#2563EB"),
                    rx.text("Target Encoding Builder", color="#111827"),
                    spacing="2", align="center",
                ),
            ),
            rx.vstack(
                rx.vstack(
                    rx.text("Aggregations:", font_size="xs", font_weight="bold", color="#111827"),
                    rx.flex(
                        rx.foreach(S.aggregation_choices, _agg_badge),
                        flex_wrap="wrap", gap="1", width="100%",
                    ),
                    spacing="1", width="100%", align_items="flex_start",
                ),
                rx.vstack(
                    rx.text("Categorical features:", font_size="xs", font_weight="bold", color="#111827"),
                    rx.cond(
                        S.categorical_columns,
                        rx.box(
                            rx.flex(rx.foreach(S.categorical_columns, _feature_badge),
                                    flex_wrap="wrap", gap="1", width="100%"),
                            max_height="160px", overflow_y="auto", width="100%",
                        ),
                        rx.text("No categorical columns available — apply the parent node first.",
                                font_size="xs", color="#F87171"),
                    ),
                    spacing="1", width="100%", align_items="flex_start",
                ),
                rx.hstack(
                    rx.text("Target:", font_size="xs", font_weight="bold", color="#111827"),
                    rx.select(
                        S.all_columns,
                        value=S.target_col,
                        on_change=S.set_target_col,
                        placeholder="target column…",
                        color="#111111", background_color="white", width="240px",
                    ),
                    spacing="2", align="center",
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
            max_width="560px",
        ),
        open=S.is_open,
        on_open_change=S.set_is_open,
    )
