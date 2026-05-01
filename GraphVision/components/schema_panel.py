import reflex as rx

from ..models.schema_state import SchemaState

_COLUMN_TYPES = ["numeric", "categorical", "ordered_categorical", "excluded"]


def _schema_row(row: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(rx.text(row["name"], font_size="sm", color="black")),
        rx.table.cell(
            rx.cond(
                row["type"] == "service",
                rx.badge("service", color_scheme="gray"),
                rx.select(
                    _COLUMN_TYPES,
                    value=row["type"],
                    on_change=SchemaState.update_row_type(row["name"]),
                    size="1",
                ),
            )
        ),
    )


def schema_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Edit schema"),
            rx.vstack(
                rx.box(
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Column"),
                                rx.table.column_header_cell("Type"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(SchemaState.rows, _schema_row),
                        ),
                        width="100%",
                    ),
                    max_height="400px",
                    overflow_y="auto",
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Cancel", variant="outline", color_scheme="gray")
                    ),
                    rx.button("Save", on_click=SchemaState.save_schema),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="500px",
        ),
        open=SchemaState.is_open,
        on_open_change=SchemaState.set_is_open,
    )
