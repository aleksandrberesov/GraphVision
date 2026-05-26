"""Base-schema constructor dialog.

Shows every dataset column with a role dropdown so the user can assign each
column to a semantic pool (target, exposure, index, force-coercions, or just
let it be auto-typed as a plain feature).
"""

import reflex as rx

from ..models.schema_state import BaseSchemaState, _ROLES

# Human-readable labels for the dropdown values.
_ROLE_LABELS: dict = {
    "none":             "Feature (auto-type)",
    "target":           "Target",
    "exposure":         "Exposure",
    "index":            "Index",
    "force_drop":       "Drop",
    "force_numeric":    "Force numeric",
    "force_datetime":   "Force datetime",
    "force_categorical": "Force categorical",
}

# Colour chips shown next to each role in the legend.
_ROLE_COLORS: dict = {
    "none":             "gray",
    "target":           "blue",
    "exposure":         "green",
    "index":            "orange",
    "force_drop":       "red",
    "force_numeric":    "cyan",
    "force_datetime":   "purple",
    "force_categorical": "pink",
}


def _role_row(item: dict, idx: int) -> rx.Component:
    """Render one {"col": name, "role": current_role} dict as a table row.

    Two-argument signature (item, idx) causes rx.foreach to pass the integer
    row index as the second arg, compiled to the JS Array.map index variable
    (``idx_rx_state_``) rather than a dict-key lookup.

    Root cause of the old bug
    -------------------------
    The previous single-arg form used ``on_change=BaseSchemaState.set_role(col_name)``
    where ``col_name = item["col"]``.  Reflex compiled this partial event arg as
    the JS expression ``item_rx_state_?.["col"]``.  In certain Radix Select ×
    Dialog timing scenarios that expression evaluated to ``undefined``; the
    socket encoder (``(k,v)=>v===undefined?null:v``) converted it to JSON
    ``null``; and the server received ``col=None``.  ``set_role(col=None)``
    silently no-oped (``item["col"]==None`` is always False) and sent back the
    entire list unchanged — all still "none".  The user saw every dropdown snap
    back to "none", which looked like "the page reloaded".

    The fix
    -------
    Using ``set_role_by_index(idx)`` with the integer index avoids all property
    lookups on the item object.  ``idx_rx_state_`` is the raw second argument of
    Array.map — always a valid integer, never undefined.
    """
    col_name = item["col"]
    current_role = item["role"]
    return rx.table.row(
        rx.table.cell(
            rx.text(col_name, size="2", font_family="monospace"),
            padding_y="1",
        ),
        rx.table.cell(
            rx.select(
                _ROLES,
                value=current_role,
                on_change=BaseSchemaState.set_role_by_index(idx),
                size="1",
                width="100%",
            ),
            padding_y="1",
            min_width="190px",
        ),
    )


def schema_constructor_panel() -> rx.Component:
    """Dialog for building / editing the base schema role assignments.

    on_open_change is intentionally absent from rx.dialog.root.
    ---------------------------------------------------------------
    Radix UI renders the rx.select dropdown in a portal outside the dialog DOM.
    When the user clicks a dropdown option, Radix's DismissableLayer sees that
    pointer-down as an "outside" interaction and fires onOpenChange(false),
    which closes the dialog before the role is committed.  The user perceives
    this as the page reloading with their selection reverted to "none".

    Because open=BaseSchemaState.constructor_open makes this a fully controlled
    dialog, omitting onOpenChange means Radix has no handler to call — outside
    clicks and Escape are silently ignored, and only the Cancel / Apply buttons
    (which set constructor_open directly) can dismiss the dialog.
    """
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Base schema constructor"),
                rx.text(
                    "Assign a role to each column. "
                    "'Feature (auto-type)' columns are typed automatically "
                    "from the data; all others become service columns.",
                    size="2",
                    color_scheme="gray",
                ),
                # Legend strip
                rx.hstack(
                    *[
                        rx.badge(
                            _ROLE_LABELS[r],
                            color_scheme=_ROLE_COLORS[r],
                            size="1",
                            variant="soft",
                        )
                        for r in _ROLES
                    ],
                    wrap="wrap",
                    spacing="1",
                ),
                # Scrollable column table
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Column"),
                                rx.table.column_header_cell("Role"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                BaseSchemaState.column_role_items,
                                _role_row,
                            ),
                        ),
                        width="100%",
                    ),
                    max_height="420px",
                    overflow_y="auto",
                    width="100%",
                    border="1px solid #e5e7eb",
                    border_radius="6px",
                ),
                # Action buttons
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="outline",
                        color_scheme="gray",
                        on_click=BaseSchemaState.set_constructor_open(False),
                    ),
                    rx.button(
                        "Apply",
                        on_click=BaseSchemaState.apply_constructor,
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
        open=BaseSchemaState.constructor_open,
        # on_open_change deliberately omitted — see docstring above.
    )
