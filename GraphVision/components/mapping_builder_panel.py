"""
Category Mapping Builder dialog (Phase 4 — multi-select → merge).

Pick categorical columns; for the active column, sort/search its values (chips show
frequency %), multi-select several, name a group, and Merge them. Produces the same
GLMCategoryMappingTransformation ``mappings`` dict as before.
"""

import reflex as rx

from ..models.mapping_builder_state import MappingBuilderState as S


# ── column picker / switcher ─────────────────────────────────────────────────

def _column_badge(col: str) -> rx.Component:
    is_selected = S.selected_features.contains(col)  # type: ignore[attr-defined]
    is_active = S.active_column == col
    return rx.badge(
        col,
        on_click=S.toggle_feature(col),
        cursor="pointer",
        color_scheme=rx.cond(  # type: ignore[arg-type]
            is_active, "blue", rx.cond(is_selected, "green", "gray"),
        ),
        variant=rx.cond(is_selected, "solid", "surface"),  # type: ignore[arg-type]
        font_size="xs",
    )


def _col_tab(col: str) -> rx.Component:
    is_active = S.active_column == col
    return rx.button(
        col,
        on_click=S.set_active_column(col),
        size="1",
        variant=rx.cond(is_active, "solid", "surface"),  # type: ignore[arg-type]
        color_scheme="blue",
    )


# ── value chip + merged-group summary row ────────────────────────────────────

def _value_chip(item: dict) -> rx.Component:
    return rx.badge(
        item["label"].to(str),  # type: ignore[attr-defined]
        on_click=S.toggle_value(item["value"]),
        cursor="pointer",
        color_scheme=rx.cond(  # type: ignore[arg-type]
            item["is_selected"], "green",
            rx.cond(item["is_merged"], "blue", "gray"),
        ),
        variant=rx.cond(item["is_selected"], "solid", "surface"),  # type: ignore[arg-type]
        font_size="xs",
    )


def _merged_row(row: dict) -> rx.Component:
    return rx.hstack(
        rx.icon("git-merge", size=12, color="#2563EB"),
        rx.text(
            row["group"].to(str) + "  ←  " + row["members"].to(str),  # type: ignore[attr-defined]
            font_size="xs", color="#374151",
            overflow="hidden", text_overflow="ellipsis", white_space="nowrap",
        ),
        spacing="1", align="center", width="100%",
    )


def _sort_button(label: str, mode: str) -> rx.Component:
    return rx.button(
        label,
        on_click=S.set_sort_mode(mode),
        size="1",
        variant=rx.cond(S.sort_mode == mode, "solid", "soft"),  # type: ignore[arg-type]
        color_scheme="gray",
    )


# ── active-column editor ─────────────────────────────────────────────────────

def _active_editor() -> rx.Component:
    return rx.vstack(
        rx.divider(color="#E5E7EB"),
        rx.hstack(
            rx.text("Values of", font_size="xs", color="#9CA3AF"),
            rx.text(S.active_column, font_size="xs", font_weight="bold", color="#111827"),
            rx.spacer(),
            rx.text("Sort:", font_size="xs", color="#9CA3AF"),
            _sort_button("Frequency", "frequency"),
            _sort_button("A–Z", "alphabet"),
            spacing="2", align="center", width="100%",
        ),
        rx.hstack(
            rx.input(
                value=S.search,
                on_change=S.set_search,
                placeholder="Search values…",
                size="1", width="60%", color="#111111", background_color="white",
            ),
            rx.spacer(),
            rx.checkbox(
                "Hide merged",
                checked=S.hide_merged,
                on_change=S.set_hide_merged,
                size="1",
            ),
            width="100%", align="center",
        ),
        # value chips
        rx.box(
            rx.flex(
                rx.foreach(S.active_values_view, _value_chip),
                flex_wrap="wrap", gap="1", width="100%",
            ),
            max_height="160px", overflow_y="auto", width="100%",
        ),
        # merge controls
        rx.hstack(
            rx.input(
                value=S.group_name,
                on_change=S.set_group_name,
                placeholder="Group name (e.g. Lada)…",
                size="1", width="46%", color="#111111", background_color="white",
            ),
            rx.button(
                rx.hstack(rx.icon("git-merge", size=14), rx.text("Merge"),
                          spacing="1", align="center"),
                on_click=S.merge,
                disabled=~S.can_merge,  # type: ignore[operator]
                size="1", color_scheme="blue",
            ),
            rx.button("Reset", on_click=S.reset_selection, size="1",
                      variant="soft", color_scheme="gray"),
            rx.button("Clear", on_click=S.clear_merges, size="1",
                      variant="soft", color_scheme="red"),
            spacing="2", align="center", width="100%",
        ),
        # merged-group summary
        rx.cond(
            S.merged_groups.length() > 0,
            rx.vstack(
                rx.text("Groups:", font_size="xs", font_weight="bold", color="#111827"),
                rx.box(
                    rx.vstack(rx.foreach(S.merged_groups, _merged_row),
                              spacing="1", width="100%"),
                    max_height="100px", overflow_y="auto", width="100%",
                ),
                spacing="1", width="100%", align_items="flex_start",
            ),
        ),
        spacing="2", width="100%", align_items="flex_start",
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
                    spacing="2", align="center",
                ),
            ),
            rx.vstack(
                # ── column picker ────────────────────────────────────────
                rx.vstack(
                    rx.text("Select columns to map:", font_size="xs",
                            font_weight="bold", color="#111827"),
                    rx.cond(
                        S.available_columns,
                        rx.flex(
                            rx.foreach(S.available_columns, _column_badge),
                            flex_wrap="wrap", gap="1", width="100%",
                        ),
                        rx.text("No categorical columns available — apply the parent node first.",
                                font_size="xs", color="#F87171"),
                    ),
                    spacing="1", width="100%", align_items="flex_start",
                ),

                # ── column switcher (when multiple columns selected) ──────
                rx.cond(
                    S.selected_features.length() > 1,
                    rx.hstack(
                        rx.text("Edit column:", font_size="xs", color="#9CA3AF"),
                        rx.flex(rx.foreach(S.selected_features, _col_tab),
                                flex_wrap="wrap", gap="1"),
                        align="center", spacing="2", width="100%",
                    ),
                ),

                # ── active-column merge editor ───────────────────────────
                rx.cond(S.active_column != "", _active_editor()),

                rx.divider(color="#E5E7EB"),

                # ── other params ─────────────────────────────────────────
                rx.hstack(
                    rx.text("Unknown strategy:", font_size="xs", color="#111827"),
                    rx.select(
                        ["ignore", "unknown", "most_frequent"],
                        value=S.unknown_strategy,
                        on_change=S.set_unknown_strategy,
                        size="1", color="#111111", background_color="white", width="160px",
                    ),
                    rx.spacer(),
                    rx.text("Keep original:", font_size="xs", color="#111827"),
                    rx.select(
                        ["true", "false"],
                        value=rx.cond(S.keep_original, "true", "false"),
                        on_change=S.set_keep_original,
                        size="1", color="#111111", background_color="white", width="90px",
                    ),
                    spacing="2", align="center", width="100%",
                ),

                # ── action buttons ───────────────────────────────────────
                rx.hstack(
                    rx.button("Cancel", on_click=S.close, variant="soft", color_scheme="brown"),
                    rx.button(
                        rx.cond(S.is_edit_mode, "Save", "Apply"),
                        on_click=S.submit,
                        disabled=~S.can_submit,  # type: ignore[operator]
                        color_scheme="blue",
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background_color="white",
            max_width="580px",
            max_height="85vh",
            overflow_y="auto",
        ),
        open=S.is_open,
        on_open_change=S.set_is_open,
    )
