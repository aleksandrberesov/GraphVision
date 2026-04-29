import reflex as rx
from ..models import GraphState as State


def upload_box():
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button("Create / load graph", width="100%"),
        ),
        rx.dialog.content(
            rx.dialog.title("Create or load graph"),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("New graph", value="new"),
                    rx.tabs.trigger("Load graph", value="load"),
                ),
                rx.tabs.content(
                    rx.vstack(
                        rx.text("Dataset (CSV / Parquet)", font_weight="bold", color="black"),
                        rx.upload(
                            rx.vstack(
                                rx.icon(tag="cloud_upload", color="#2563eb"),
                                rx.text("Click or drag dataset here", color="#1d4ed8"),
                                align="center",
                            ),
                            id="dataset_upload",
                            on_drop=State.handle_dataset_upload(
                                rx.upload_files("dataset_upload")
                            ),
                            multiple=False,
                            border="1px dashed #2563eb",
                            padding="2em",
                            width="100%",
                        ),
                        rx.cond(
                            State.uploaded_dataset_file != "",
                            rx.text(
                                State.uploaded_dataset_file,
                                color="green",
                                font_size="sm",
                            ),
                            rx.fragment(),
                        ),
                        rx.text(
                            "Schema (JSON / YAML, optional)",
                            font_weight="bold",
                            color="black",
                        ),
                        rx.upload(
                            rx.vstack(
                                rx.icon(tag="cloud_upload", color="#6B7280"),
                                rx.text("Click or drag schema here", color="#6B7280"),
                                align="center",
                            ),
                            id="schema_upload",
                            on_drop=State.handle_schema_upload(
                                rx.upload_files("schema_upload")
                            ),
                            multiple=False,
                            border="1px dashed #9CA3AF",
                            padding="2em",
                            width="100%",
                        ),
                        rx.cond(
                            State.uploaded_schema_file != "",
                            rx.text(
                                State.uploaded_schema_file,
                                color="green",
                                font_size="sm",
                            ),
                            rx.fragment(),
                        ),
                        rx.hstack(
                            rx.dialog.close(
                                rx.button(
                                    "Cancel",
                                    variant="outline",
                                    color_scheme="gray",
                                ),
                            ),
                            rx.button(
                                "Create",
                                on_click=State.create_graph_with_data,
                                disabled=State.uploaded_dataset_file == "",
                            ),
                            spacing="3",
                            justify="end",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    value="new",
                ),
                rx.tabs.content(
                    rx.vstack(
                        rx.upload(
                            rx.vstack(
                                rx.icon(tag="cloud_upload", color="#2563eb"),
                                rx.text(
                                    "Click or drag JSON graph here",
                                    color="#1d4ed8",
                                ),
                                align="center",
                            ),
                            id="json_upload",
                            on_drop=State.handle_json_upload(
                                rx.upload_files("json_upload")
                            ),
                            multiple=False,
                            border="1px dashed #2563eb",
                            padding="2em",
                            width="100%",
                        ),
                        rx.cond(
                            State.uploaded_file != "",
                            rx.text(
                                State.uploaded_file,
                                color="green",
                                font_size="sm",
                            ),
                            rx.fragment(),
                        ),
                        rx.hstack(
                            rx.dialog.close(
                                rx.button(
                                    "Cancel",
                                    variant="outline",
                                    color_scheme="gray",
                                ),
                            ),
                            spacing="3",
                            justify="end",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    value="load",
                ),
                default_value="new",
                width="100%",
            ),
            max_width="480px",
        ),
        open=State.upload_dialog_open,
        on_open_change=State.set_upload_dialog_open,
    )
