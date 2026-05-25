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


def _role_row(pair: list) -> rx.Component:
    """Render one [col_name, current_role] pair as a table row."""
    col_name: str = pair[0]
    current_role: str = pair[1]
    return rx.table.row(
        rx.table.cell(
            rx.text(col_name, size="2", font_family="monospace"),
            padding_y="1",
        ),
        rx.table.cell(
            rx.select(
                _ROLES,
                value=current_role,
                on_change=BaseSchemaState.set_role(col_name),
                size="1",
                width="100%",
            ),
            padding_y="1",
            min_width="190px",
        ),
    )


def schema_constructor_panel() -> rx.Component:
    """Dialog for building / editing the base schema role assignments."""
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
                                BaseSchemaState.column_roles_list,
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
        on_open_change=BaseSchemaState.set_constructor_open,
    )
