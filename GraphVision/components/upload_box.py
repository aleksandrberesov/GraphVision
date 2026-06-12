import reflex as rx
from ..models import GraphState as State, DialogState


def upload_box():
    return rx.fragment(
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Create graph"),
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
                            rx.upload_files("dataset_upload") # type: ignore[arg-type]
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
                            rx.upload_files("schema_upload") # type: ignore[arg-type]
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
                max_width="480px",
            ),
            open=DialogState.create_open,
            on_open_change=DialogState.set_create_open,
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Download project"),
                rx.vstack(
                    rx.text("File name", font_weight="bold", color="black"),
                    rx.hstack(
                        rx.input(
                            value=DialogState.save_filename,
                            on_change=DialogState.set_save_filename,
                            placeholder="project-name",
                            flex="1",
                        ),
                        rx.text(".yaml", color="gray", white_space="nowrap"),
                        align="center",
                        width="100%",
                    ),
                    rx.text("Data inclusion", font_weight="bold", color="black"),
                    rx.radio_group.root(
                        rx.vstack(
                            rx.radio_group.item("Structure only — pipeline + schemas, no data",
                                                value="structure_only"),
                            rx.radio_group.item("Full project — embed dataset as CSV",
                                                value="full"),
                            rx.radio_group.item("Full project — embed dataset as Parquet (smaller)",
                                                value="full_parquet"),
                            spacing="2",
                            align="start",
                        ),
                        value=DialogState.download_mode,
                        on_change=DialogState.set_download_mode,
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
                            "Download",
                            on_click=State.download_project,
                            disabled=DialogState.save_filename.strip() == "",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                max_width="420px",
            ),
            open=DialogState.save_open,
            on_open_change=DialogState.set_save_open,
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Upload project"),
                rx.vstack(
                    rx.upload(
                        rx.vstack(
                            rx.icon(tag="cloud_upload", color="#2563eb"),
                            rx.text(
                                "Click or drag project YAML here (.yaml)",
                                color="#1d4ed8",
                            ),
                            align="center",
                        ),
                        id="yaml_upload",
                        on_drop=State.handle_yaml_stage(
                            rx.upload_files("yaml_upload")  # type: ignore[arg-type]
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
                        rx.button(
                            "Upload",
                            on_click=State.handle_yaml_upload,
                            disabled=State.uploaded_file == "",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                max_width="480px",
            ),
            open=DialogState.load_open,
            on_open_change=DialogState.set_load_open,
        ),
        # Import-rename dialog — shown when the uploaded YAML has a name that
        # already exists among the user's saved projects.
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Project name already exists"),
                rx.vstack(
                    rx.text(
                        "A project named ",
                        rx.text.strong(DialogState.import_conflict_name),
                        " already exists. Enter a new name to import it under:",
                        color="#111827",
                    ),
                    rx.input(
                        value=DialogState.import_rename_value,
                        on_change=DialogState.set_import_rename_value,
                        placeholder="new-project-name",
                        width="100%",
                        auto_focus=True,
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            variant="outline",
                            color_scheme="gray",
                            on_click=[
                                DialogState.set_import_rename_open(False),
                                State.clear_staged_yaml,
                            ],
                        ),
                        rx.button(
                            "Import",
                            on_click=State.handle_yaml_upload_with_override,
                            disabled=DialogState.import_rename_value.strip() == "",
                        ),
                        spacing="3",
                        justify="end",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                max_width="420px",
            ),
            open=DialogState.import_rename_open,
            on_open_change=DialogState.set_import_rename_open,
        ),
    )
