"""
GLM model node configuration dialog (guided flow — Phase 5, option A).

Walks the user through: (1) pick the feature columns that go to the model and
check their stability, (2) choose the GLM family + link, (3) preview the GLM
formula — then "Create model" auto-inserts a ColumnRemover (dropping the
unselected columns) and an under-the-hood column-name transliterator upstream of
the model node in one action.
"""

import reflex as rx

from ..models.model_config_state import ModelConfigState


def _section_title(text: str) -> rx.Component:
    return rx.text(text, font_size="xs", font_weight="bold", color="#111827")


def _columns_section() -> rx.Component:
    return rx.vstack(
        _section_title("1 · Columns into the model"),
        rx.text(
            "Selected (green) columns go to the model; unselected (gray) are dropped.",
            font_size="xs", color="#6B7280",
        ),
        rx.hstack(
            rx.button("Select all", on_click=ModelConfigState.select_all_columns,
                      size="1", variant="soft", color_scheme="gray"),
            rx.button("Clear", on_click=ModelConfigState.clear_columns,
                      size="1", variant="soft", color_scheme="gray"),
            rx.spacer(),
            rx.text(
                ModelConfigState.removed_preview.length().to_string() + " dropped",
                font_size="xs", color="#9CA3AF",
            ),
            width="100%", align_items="center",
        ),
        rx.flex(
            rx.foreach(
                ModelConfigState.available_columns,
                lambda col: rx.badge(
                    col,
                    color_scheme=rx.cond(
                        ModelConfigState.selected_columns.contains(col), "green", "gray"
                    ),
                    variant="soft",
                    cursor="pointer",
                    on_click=ModelConfigState.toggle_column(col),
                ),
            ),
            flex_wrap="wrap", gap="1", width="100%",
            max_height="120px", overflow_y="auto",
        ),
        rx.hstack(
            rx.button("Recompute stability",
                      on_click=ModelConfigState.recompute_stability,
                      size="1", variant="soft", color_scheme="blue"),
            rx.text(ModelConfigState.stability_text, font_size="xs", color="#374151"),
            spacing="2", align_items="center", width="100%",
        ),
        spacing="2", width="100%", align_items="flex_start",
    )


def _family_link_section() -> rx.Component:
    return rx.vstack(
        _section_title("2 · GLM family & link"),
        rx.hstack(
            rx.vstack(
                rx.text("Family", font_size="xs", color="#6B7280"),
                rx.select(
                    ModelConfigState.family_names,
                    value=ModelConfigState.selected_family,
                    on_change=ModelConfigState.set_family,
                    width="100%", color="#111111", background_color="white",
                ),
                spacing="1", width="50%", align_items="flex_start",
            ),
            rx.vstack(
                rx.text("Link", font_size="xs", color="#6B7280"),
                rx.select(
                    ModelConfigState.available_links,
                    value=ModelConfigState.selected_link,
                    on_change=ModelConfigState.set_link,
                    width="100%", color="#111111", background_color="white",
                ),
                rx.text(
                    rx.text.span("Canonical: ", color="#6B7280", font_size="xs"),
                    rx.text.span(ModelConfigState.canonical_link,
                                 color="#2563EB", font_size="xs"),
                ),
                spacing="1", width="50%", align_items="flex_start",
            ),
            spacing="3", width="100%",
        ),
        spacing="2", width="100%", align_items="flex_start",
    )


def _formula_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            _section_title("3 · GLM formula"),
            rx.spacer(),
            rx.button("Preview formula", on_click=ModelConfigState.preview_formula,
                      size="1", variant="soft", color_scheme="violet"),
            width="100%", align_items="center",
        ),
        rx.cond(
            ModelConfigState.formula_text != "",
            rx.code_block(
                ModelConfigState.formula_text,
                language="r",
                wrap_long_lines=True,
                width="100%",
                font_size="xs",
            ),
            rx.text("Click “Preview formula” to see the GLM equation.",
                    font_size="xs", color="#9CA3AF"),
        ),
        rx.cond(
            ModelConfigState.formula_warning != "",
            rx.callout.root(
                rx.callout.text(ModelConfigState.formula_warning, font_size="xs"),
                color="amber", size="1",
            ),
        ),
        spacing="2", width="100%", align_items="flex_start",
    )


def model_config_panel() -> rx.Component:
    """GLM model configuration dialog (rendered once in the page layout)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("cpu", size=16, color="#7C3AED"),
                    rx.text("Add GLM Model", color="#111827"),
                    spacing="2", align="center",
                ),
            ),
            rx.vstack(
                rx.box(
                    rx.text(
                        "Pick the features, choose a family/link, preview the formula, "
                        "then create the model. A column-name transliterator is applied "
                        "under the hood. Fit the model from its node afterwards.",
                        font_size="xs", color="#6B7280",
                    ),
                    padding="2", border_radius="4px", background="#F3F4F6", width="100%",
                ),
                _columns_section(),
                rx.divider(),
                _family_link_section(),
                rx.divider(),
                _formula_section(),
                rx.hstack(
                    rx.button("Cancel", on_click=ModelConfigState.close,
                              variant="soft", color_scheme="gray"),
                    rx.button(
                        "Create model",
                        on_click=ModelConfigState.apply,
                        disabled=~ModelConfigState.can_apply,  # type: ignore[operator]
                        color_scheme="violet",
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background_color="white",
            max_width="520px",
            max_height="85vh",
            overflow_y="auto",
        ),
        open=ModelConfigState.is_open,
        on_open_change=ModelConfigState.set_is_open,
    )
