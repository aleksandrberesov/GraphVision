"""Base-schema constructor dialog.

Two-tier role model (mirrors the notebook MultiTabSelector):

  Tier-1 — exclusive (target / index / exposure / none)
    Each column holds at most one tier-1 role.  Clicking a badge assigns it;
    clicking the same badge again reverts to "none".  The three role-sections
    (target, index, exposure) are visually separated from the type-override
    sections by a divider.

    Exposure extras:
      • Only numeric columns are selectable — non-numeric badges are dimmed
        and have pointer-events disabled so they cannot be clicked.
      • Multi-select: several columns may hold the exposure role (the base
        schema's exposure pool). The Tiny Schema later picks the one working
        exposure used as model weights.

  Tier-2 — independent flags (force_drop / force_numeric / force_datetime / force_categorical)
    Each flag is a boolean independent of the tier-1 role and of every other
    flag.  A column can simultaneously be "target" AND "force_categorical".
    Clicking toggles the flag without touching the tier-1 role.

on_open_change is intentionally absent from rx.dialog.root.
---------------------------------------------------------------
Radix UI renders portals (dropdowns, tooltips) outside the dialog DOM.
With on_open_change present, Radix's DismissableLayer fires
onOpenChange(false) on portal interactions, closing the dialog before the
selection is committed.  Omitting the handler means only the Cancel /
Apply buttons can dismiss the dialog.
"""

import reflex as rx

from ..models.schema_state import BaseSchemaState, _ROLES, _TIER1_ROLES, _TIER2_FLAGS

# Human-readable labels for each role.
_ROLE_LABELS: dict = {
    "none":              "Feature (auto-type)",
    "target":            "Target",
    "exposure":          "Exposure  ·  numeric only",
    "index":             "Index",
    "force_drop":        "Drop",
    "force_numeric":     "Force numeric",
    "force_datetime":    "Force datetime",
    "force_categorical": "Force categorical",
}

# Colour schemes for badges.
_ROLE_COLORS: dict = {
    "none":              "gray",
    "target":            "blue",
    "exposure":          "green",
    "index":             "orange",
    "force_drop":        "red",
    "force_numeric":     "cyan",
    "force_datetime":    "purple",
    "force_categorical": "pink",
}

# Display order within each tier.
_TIER1_ORDER = ["none", "target", "exposure", "index"]
_TIER2_ORDER = ["force_drop", "force_numeric", "force_datetime", "force_categorical"]


def _make_badge_fn(role: str):
    """Factory: return a two-arg foreach callback for one role section.

    Tier-1 roles use toggle_tier1_by_index and read item["role"].
    Tier-2 flags use toggle_tier2_by_index and read item[flag] (boolean).

    Each function is given a unique __name__ / __qualname__ so Reflex's
    component registry treats the 8 callbacks as distinct entries.
    """
    color = _ROLE_COLORS[role]
    is_tier2 = role in _TIER2_FLAGS

    def _badge(item: dict, idx: int) -> rx.Component:
        if is_tier2:
            # Independent boolean flag — always clickable.
            is_selected = item[role]
            return rx.tooltip(
                rx.badge(
                    item["col"],
                    color_scheme=rx.cond(is_selected, color, "gray"),  # type: ignore[arg-type]
                    variant=rx.cond(is_selected, "solid", "surface"),  # type: ignore[arg-type]
                    on_click=BaseSchemaState.toggle_tier2_by_index(idx, role),
                    cursor="pointer",
                    font_family="monospace",
                    font_size="11px",
                    user_select="none",
                ),
                content=item["col"].to(str) + "  ·  " + item["val0"].to(str) + "  /  " + item["val1"].to(str),
                delay_duration=300,
            )

        # Tier-1 role — mutually exclusive within target / index / exposure / none.
        is_selected = item["role"] == role

        if role == "exposure":
            # Non-numeric columns are blocked: dimmed, cursor not-allowed, no pointer events.
            return rx.tooltip(
                rx.badge(
                    item["col"],
                    color_scheme=rx.cond(is_selected, color, "gray"),  # type: ignore[arg-type]
                    variant=rx.cond(is_selected, "solid", "surface"),  # type: ignore[arg-type]
                    on_click=BaseSchemaState.toggle_tier1_by_index(idx, role),
                    cursor=rx.cond(item["is_numeric"], "pointer", "not-allowed"),  # type: ignore[arg-type]
                    opacity=rx.cond(item["is_numeric"], "1", "0.35"),  # type: ignore[arg-type]
                    pointer_events=rx.cond(item["is_numeric"], "auto", "none"),  # type: ignore[arg-type]
                    font_family="monospace",
                    font_size="11px",
                    user_select="none",
                ),
                content=item["col"].to(str) + "  ·  " + item["val0"].to(str) + "  /  " + item["val1"].to(str),
                delay_duration=300,
            )

        # All other tier-1 sections (none / target / index) — always clickable.
        return rx.tooltip(
            rx.badge(
                item["col"],
                color_scheme=rx.cond(is_selected, color, "gray"),  # type: ignore[arg-type]
                variant=rx.cond(is_selected, "solid", "surface"),  # type: ignore[arg-type]
                on_click=BaseSchemaState.toggle_tier1_by_index(idx, role),
                cursor="pointer",
                font_family="monospace",
                font_size="11px",
                user_select="none",
            ),
            content=item["col"].to(str) + "  ·  " + item["val0"].to(str) + "  /  " + item["val1"].to(str),
            delay_duration=300,
        )

    _badge.__name__ = f"_badge_{role}"
    _badge.__qualname__ = f"_badge_{role}"
    return _badge


# One uniquely-named callback per role, built once at module load time.
_BADGE_FNS: dict = {role: _make_badge_fn(role) for role in _ROLES}


# Tier-1 roles the user must assign at least one column to before applying.
_REQUIRED_ROLES: set = {"target", "index"}
# Tier-1 roles that are optional (no blocking validation).
_OPTIONAL_ROLES: set = {"exposure"}


def _create_new_control(role: str) -> rx.Component:
    """"+ Create new" button + dashed indicator for the exposure / index sections.

    Returns an empty fragment for every other role.
    """
    if role == "exposure":
        active = BaseSchemaState.create_exposure
        name = BaseSchemaState.reserve_exposure_name
        on_click = BaseSchemaState.create_new_exposure
        disabled = BaseSchemaState.has_exposure_assigned
    elif role == "index":
        active = BaseSchemaState.create_index
        name = BaseSchemaState.reserve_index_name
        on_click = BaseSchemaState.create_new_index
        disabled = False
    else:
        return rx.fragment()

    color = _ROLE_COLORS[role]
    return rx.hstack(
        rx.button(
            rx.cond(active, "✕ Remove new column", "+ Create new"),
            on_click=on_click,
            size="1",
            variant="soft",
            color_scheme=color,
            disabled=disabled,
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
        padding_top="2",
    )


def _role_section(role: str) -> rx.Component:
    """One role section: labelled header + all columns as badge pickers."""
    if role in _REQUIRED_ROLES:
        indicator = rx.text("*", color="#ff6b6b", font_size="12px", line_height="1")
    elif role in _OPTIONAL_ROLES:
        indicator = rx.text("optional", color="#9CA3AF", font_size="11px")
    else:
        indicator = rx.fragment()

    return rx.box(
        rx.hstack(
            rx.badge(
                _ROLE_LABELS[role],
                color_scheme=_ROLE_COLORS[role],
                size="2",
                variant="soft",
            ),
            indicator,
            spacing="1",
            align="center",
        ),
        rx.flex(
            rx.foreach(BaseSchemaState.column_role_items, _BADGE_FNS[role]),
            wrap="wrap",
            gap="1",
            padding_top="2",
        ),
        _create_new_control(role),
        padding="3",
        border_radius="6px",
        border="1px solid #e5e7eb",
        width="100%",
    )


def schema_constructor_panel() -> rx.Component:
    """Dialog for building / editing the base schema role assignments."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Base schema constructor", color="#111827"),
                rx.text(
                    "Click a column badge to assign it to a role. "
                    "Click it again to remove it. "
                    "Tier-1 roles (top group) are exclusive; "
                    "type overrides (bottom group) are independent flags.",
                    size="2",
                    color="#374151",
                ),
                # Scrollable role sections
                rx.box(
                    rx.vstack(
                        # Tier-1: exclusive role assignment
                        rx.text(
                            "Column roles  ·  exclusive",
                            size="1",
                            color="#374151",
                            weight="medium",
                        ),
                        *[_role_section(role) for role in _TIER1_ORDER],
                        rx.divider(),
                        # Tier-2: independent type-override flags
                        rx.text(
                            "Type overrides  ·  independent",
                            size="1",
                            color="#374151",
                            weight="medium",
                        ),
                        *[_role_section(role) for role in _TIER2_ORDER],
                        spacing="3",
                        width="100%",
                    ),
                    max_height="500px",
                    overflow_y="auto",
                    width="100%",
                ),
                # Validation hint shown when required roles are unassigned
                rx.cond(
                    ~BaseSchemaState.can_apply,  # type: ignore[operator]
                    rx.text(
                        "* Assign at least one Target and one Index column to apply.",
                        size="1",
                        color="#ff6b6b",
                    ),
                    rx.fragment(),
                ),
                # Action buttons
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="brown",
                        on_click=BaseSchemaState.set_constructor_open(False),
                    ),
                    rx.button(
                        "Apply",
                        on_click=BaseSchemaState.apply_constructor,
                        disabled=~BaseSchemaState.can_apply,  # type: ignore[operator]
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            background_color="white",
            max_width="620px",
        ),
        open=BaseSchemaState.constructor_open,
        # on_open_change deliberately omitted — see module docstring.
    )
