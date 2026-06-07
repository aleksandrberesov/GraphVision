"""
Category Mapping Builder dialog.

Visual builder for GLMCategoryMappingTransformation's 'mappings' param.
The user picks categorical columns, sees their unique values, and assigns
a group label to each value. On submit the full mappings dict is built
automatically.
"""

from typing import Dict

import reflex as rx

from ..models.mapping_builder_state import MappingBuilderState


# ── column picker ─────────────────────────────────────────────────────────────

def _column_badge(col: str) -> rx.Component:
    is_selected = MappingBuilderState.selected_features.contains(col)  # type: ignore[attr-defined]
    is_active = MappingBuilderState.active_column == col
    return rx.badge(
        col,
        on_click=MappingBuilderState.toggle_feature(col),
        cursor="pointer",
        color_scheme=rx.cond(  # type: ignore[arg-type]
            is_active,
            "blue",
            rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        ),
        variant=rx.cond(is_selected, "solid", "outline"),  # type: ignore[arg-type]
        font_size="xs",
    )


# ── column switcher tabs (shown below the mapping table) ─────────────────────

def _col_tab(col: str) -> rx.Component:
    is_active = MappingBuilderState.active_column == col
    return rx.button(
        col,
        on_click=MappingBuilderState.set_active_column(col),
        size="1",
        variant=rx.cond(is_active, "solid", "outline"),  # type: ignore[arg-type]
        color_scheme="blue",
    )


# ── mapping table rows ────────────────────────────────────────────────────────

def _mapping_row(row: Dict[str, str]) -> rx.Component:
    return rx.hstack(
        rx.text(
            row["value"],
            width="42%",
            color="#111827",
            font_size="sm",
            overflow="hidden",
            text_overflow="ellipsis",
            white_space="nowrap",
        ),
        rx.icon("arrow-right", size=12, color="#9CA3AF"),
        rx.input(
            value=row["group"],
            on_change=MappingBuilderState.update_row_group(row["value"]),
            size="1",
            width="42%",
            color="#111111",
            background_color="white",
        ),
        width="100%",
        align="center",
        spacing="2",
    )


# ── public component ──────────────────────────────────────────────────────────

def mapping_builder_panel() -> rx.Component:
    """Category Mapping Builder dialog (rendered once in the page layout)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("tags", size=16, color="#2563EB"),
                    rx.text("Category Mapping Builder", color="#111827"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                # ── column picker ────────────────────────────────────────
                rx.vstack(
                    rx.text(
                        "Select columns to map:",
                        font_size="xs",
                        font_weight="bold",
                        color="#111827",
                    ),
                    rx.cond(
                        MappingBuilderState.available_columns,
                        rx.flex(
                            rx.foreach(MappingBuilderState.available_columns, _column_badge),
                            flex_wrap="wrap",
                            gap="1",
                            width="100%",
                        ),
                        rx.text(
                            "No categorical columns available — apply the parent node first.",
                            font_size="xs",
                            color="#F87171",
                        ),
                    ),
                    spacing="1",
                    width="100%",
                    align_items="flex_start",
                ),

                # ── mapping table for the active column ──────────────────
                rx.cond(
                    MappingBuilderState.active_column != "",
                    rx.vstack(
                        rx.divider(color="#374151"),
                        rx.hstack(
                            rx.text("Mapping:", font_size="xs", color="#9CA3AF"),
                            rx.text(
                                MappingBuilderState.active_column,
                                font_size="xs",
                                font_weight="bold",
                                color="#111827",
                            ),
                            spacing="1",
                        ),
                        # Column header
                        rx.hstack(
                            rx.text("Original value", font_size="xs", color="#6B7280", width="42%"),
                            rx.text("", width="12px"),
                            rx.text("Group label", font_size="xs", color="#6B7280", width="42%"),
                            width="100%",
                        ),
                        # Rows
                        rx.cond(
                            MappingBuilderState.active_rows,
                            rx.box(
                                rx.vstack(
                                    rx.foreach(MappingBuilderState.active_rows, _mapping_row),
                                    spacing="1",
                                    width="100%",
                                ),
                                max_height="200px",
                                overflow_y="auto",
                                width="100%",
                            ),
                            rx.text("Loading values…", font_size="xs", color="#9CA3AF"),
                        ),
                        spacing="2",
                        width="100%",
                        align_items="flex_start",
                    ),
                    rx.fragment(),
                ),

                # ── column switcher (when multiple columns selected) ──────
                rx.cond(
                    MappingBuilderState.selected_features,
                    rx.vstack(
                        rx.divider(color="#374151"),
                        rx.hstack(
                            rx.text("Edit column:", font_size="xs", color="#9CA3AF"),
                            rx.flex(
                                rx.foreach(MappingBuilderState.selected_features, _col_tab),
                                flex_wrap="wrap",
                                gap="1",
                            ),
                            align="center",
                            spacing="2",
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.fragment(),
                ),

                rx.divider(color="#374151"),

                # ── other params ─────────────────────────────────────────
                rx.hstack(
                    rx.text("Unknown strategy:", font_size="xs", color="#111827"),
                    rx.select(
                        ["ignore", "unknown", "most_frequent"],
                        value=MappingBuilderState.unknown_strategy,
                        on_change=MappingBuilderState.set_unknown_strategy,
                        size="1",
                        color="#111111",
                        background_color="white",
                        width="180px",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text("Keep original:", font_size="xs", color="#111827"),
                    rx.select(
                        ["true", "false"],
                        value=rx.cond(MappingBuilderState.keep_original, "true", "false"),
                        on_change=MappingBuilderState.set_keep_original,
                        size="1",
                        color="#111111",
                        background_color="white",
                        width="100px",
                    ),
                    spacing="2",
                    align="center",
                ),

                # ── action buttons ───────────────────────────────────────
                rx.hstack(
                    rx.button(
                        "Cancel",
                        on_click=MappingBuilderState.close,
                        variant="outline",
                        color_scheme="gray",
                    ),
                    rx.button(
                        rx.cond(MappingBuilderState.is_edit_mode, "Save", "Add"),
                        on_click=MappingBuilderState.submit,
                        disabled=~MappingBuilderState.can_submit,  # type: ignore[operator]
                        color_scheme="blue",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="560px",
        ),
        open=MappingBuilderState.is_open,
        on_open_change=MappingBuilderState.set_is_open,
    )
