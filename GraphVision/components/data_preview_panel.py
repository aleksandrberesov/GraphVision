import reflex as rx

from ..models.data_preview_state import DataPreviewState


def data_preview_panel() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Dataset preview"),
            rx.vstack(
                rx.cond(
                    DataPreviewState.columns,
                    rx.vstack(
                        rx.text(
                            DataPreviewState.row_count_label,
                            font_size="xs",
                            color="gray",
                        ),
                        rx.scroll_area(
                            rx.table.root(
                                rx.table.header(
                                    rx.table.row(
                                        rx.foreach(
                                            DataPreviewState.columns,
                                            lambda col: rx.table.column_header_cell(
                                                col,
                                                font_size="xs",
                                                white_space="nowrap",
                                            ),
                                        ),
                                    ),
                                ),
                                rx.table.body(
                                    rx.foreach(
                                        DataPreviewState.rows,
                                        lambda row: rx.table.row(
                                            rx.foreach(
                                                row,
                                                lambda cell: rx.table.cell(
                                                    cell,
                                                    font_size="xs",
                                                    white_space="nowrap",
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                                size="1",
                                variant="surface",
                            ),
                            type="always",
                            scrollbars="both",
                            height="420px",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.text(
                        "No data available.",
                        color="gray",
                        font_size="sm",
                        font_style="italic",
                    ),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Close", variant="outline", color_scheme="gray"),
                    ),
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="900px",
            width="90vw",
        ),
        open=DataPreviewState.is_open,
        on_open_change=DataPreviewState.set_is_open,
    )
