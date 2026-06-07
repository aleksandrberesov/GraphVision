"""
Tiny Schema node configuration dialog.

Lets the user pick ONE target / exposure / index from the Node 0 pools, and a
feature column list that will be passed downstream to transformer nodes.
"""

import reflex as rx

from ..models.tiny_schema_state import TinySchemaState


# ── per-role badge renderers ──────────────────────────────────────────────────

def _target_badge(col: str) -> rx.Component:
    is_selected = TinySchemaState.selected_target == col  # type: ignore[operator]
    return rx.badge(
        col,
        on_click=TinySchemaState.set_target(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "blue", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),   # type: ignore[arg-type]
        font_size="xs",
        font_family="monospace",
        user_select="none",
    )


def _exposure_badge(col: str) -> rx.Component:
    is_selected = TinySchemaState.selected_exposure == col  # type: ignore[operator]
    return rx.badge(
        col,
        on_click=TinySchemaState.set_exposure(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),    # type: ignore[arg-type]
        font_size="xs",
        font_family="monospace",
        user_select="none",
    )


def _index_badge(col: str) -> rx.Component:
    is_selected = TinySchemaState.selected_index == col  # type: ignore[operator]
    return rx.badge(
        col,
        on_click=TinySchemaState.set_index(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "orange", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),     # type: ignore[arg-type]
        font_size="xs",
        font_family="monospace",
        user_select="none",
    )


def _feature_badge(col: str) -> rx.Component:
    is_selected = TinySchemaState.selected_features.contains(col)  # type: ignore[attr-defined]
    return rx.badge(
        col,
        on_click=TinySchemaState.toggle_feature(col),
        cursor="pointer",
        color_scheme=rx.cond(is_selected, "green", "gray"),  # type: ignore[arg-type]
        variant=rx.cond(is_selected, "solid", "outline"),    # type: ignore[arg-type]
        font_size="xs",
        font_family="monospace",
        user_select="none",
    )


# ── helpers ───────────────────────────────────────────────────────────────────

def _tiny_create_control(role: str) -> rx.Component:
    """"+ Create new" button + dashed indicator for the exposure / index roles."""
    if role == "exposure":
        active = TinySchemaState.create_exposure
        name = TinySchemaState.reserve_exposure_name
        on_click = TinySchemaState.create_new_exposure
        color = "green"
    else:  # index
        active = TinySchemaState.create_index
        name = TinySchemaState.reserve_index_name
        on_click = TinySchemaState.create_new_index
        color = "orange"

    return rx.hstack(
        rx.button(
            rx.cond(active, "✕ Remove new column", "+ Create new"),
            on_click=on_click,
            size="1",
            variant="soft",
            color_scheme=color,
        ),
        rx.cond(
            active,
            rx.badge(
                name + "  ·  will be created",
                color_scheme=color,
                variant="surface",
                font_family="monospace",
                font_size="11px",
                style={"border": "1px dashed currentColor"},
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="center",
    )


def _role_badges(
    label: str,
    options: rx.Var,
    badge_fn,
    required: bool = True,
    footer=None,
) -> rx.Component:
    """A labelled badge-picker for a single-select role column."""
    return rx.vstack(
        rx.hstack(
            rx.text(label, font_size="xs", font_weight="bold", color="#111827"),
            rx.cond(
                required,
                rx.text("*", color="#ff6b6b", font_size="xs"),
                rx.text("optional", color="#9CA3AF", font_size="xs"),
            ),
            spacing="1",
        ),
        rx.cond(
            options,
            rx.box(
                rx.flex(
                    rx.foreach(options, badge_fn),
                    flex_wrap="wrap",
                    gap="1",
                    width="100%",
                ),
                max_height="80px",
                overflow_y="auto",
                width="100%",
            ),
            rx.text(
                f"No {label.lower()} columns defined in base schema.",
                font_size="xs",
                color="#F87171",
            ),
        ),
        footer if footer is not None else rx.fragment(),
        spacing="1",
        width="100%",
        align_items="flex_start",
    )


def _feature_selector() -> rx.Component:
    """Multi-select badges for the feature column list."""
    return rx.vstack(
        rx.hstack(
            rx.text("Feature columns", font_size="xs", font_weight="bold", color="#111827"),
            rx.text("(columns kept and passed downstream)", font_size="xs", color="#9CA3AF"),
            spacing="2",
        ),
        # Select-all / Clear-all shortcuts
        rx.hstack(
            rx.button(
                "All",
                on_click=TinySchemaState.select_all_features,
                size="1",
                variant="ghost",
            ),
            rx.button(
                "None",
                on_click=TinySchemaState.clear_all_features,
                size="1",
                variant="ghost",
            ),
            spacing="1",
        ),
        rx.cond(
            TinySchemaState.pure_feature_options,
            rx.box(
                rx.flex(
                    rx.foreach(TinySchemaState.pure_feature_options, _feature_badge),
                    flex_wrap="wrap",
                    gap="1",
                    width="100%",
                ),
                max_height="200px",
                overflow_y="auto",
                width="100%",
            ),
            rx.text(
                "No feature columns available at this node.",
                font_size="xs",
                color="#9CA3AF",
            ),
        ),
        spacing="2",
        width="100%",
        align_items="flex_start",
    )


# ── public component ──────────────────────────────────────────────────────────

def tiny_schema_panel() -> rx.Component:
    """Tiny Schema configuration dialog (rendered once in the page layout)."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("split", size=16, color="#2563EB"),
                    rx.text("Tiny Schema", color="#111827"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.vstack(
                # Info banner
                rx.box(
                    rx.text(
                        "Sets the working target / exposure / index for this branch. "
                        "Different branches can use different Tiny Schemas.",
                        font_size="xs",
                        color="#6B7280",
                    ),
                    padding="2",
                    border_radius="4px",
                    background="#F3F4F6",
                    width="100%",
                ),

                # Role badge pickers
                _role_badges(
                    "Target",
                    TinySchemaState.target_options,
                    _target_badge,
                    required=True,
                ),
                _role_badges(
                    "Exposure",
                    TinySchemaState.exposure_options,
                    _exposure_badge,
                    required=True,
                    footer=_tiny_create_control("exposure"),
                ),
                _role_badges(
                    "Index",
                    TinySchemaState.index_options,
                    _index_badge,
                    required=True,
                    footer=_tiny_create_control("index"),
                ),

                rx.divider(color="#374151"),

                # Feature multi-select
                _feature_selector(),

                # Action buttons
                rx.hstack(
                    rx.button(
                        "Cancel",
                        on_click=TinySchemaState.close,
                        variant="outline",
                        color_scheme="gray",
                    ),
                    rx.button(
                        "Add node",
                        on_click=TinySchemaState.apply,
                        disabled=~TinySchemaState.can_apply,  # type: ignore[operator]
                        color_scheme="blue",
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="520px",
        ),
        open=TinySchemaState.is_open,
        on_open_change=TinySchemaState.set_is_open,
    )
