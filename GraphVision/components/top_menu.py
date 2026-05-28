import importlib.metadata
import os
import subprocess
from pathlib import Path

import reflex as rx

from ..models import DialogState
from ..models.auth_state import AuthState
from ..models.config_state import ConfigState
from ..models.graph import GraphState
from ..models.model_config_state import ModelConfigState
from ..models.schema_state import BaseSchemaState, SchemaState

try:
    _APP_VERSION = importlib.metadata.version("reflex_ui")
except importlib.metadata.PackageNotFoundError:
    _APP_VERSION = "dev"

try:
    # In Docker, APP_BUILD_NUMBER is injected as an env var at build time
    # (the container has no access to the parent .git tree, so git fails there).
    # In local dev, fall back to counting commits via git.
    _BUILD = os.environ.get("APP_BUILD_NUMBER", "").strip() or (
        subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=Path(__file__).parent.parent.parent,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    )
except Exception:
    _BUILD = "0"


def _project_dialogs() -> rx.Component:
    return rx.fragment(
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Open project"),
                rx.vstack(
                    rx.foreach(
                        DialogState.project_list,
                        lambda name: rx.button(
                            name,
                            variant="ghost",
                            width="100%",
                            on_click=[
                                DialogState.set_open_project_open(False),
                                GraphState.switch_project(name),
                            ],
                        ),
                    ),
                    rx.cond(
                        DialogState.project_list == [],
                        rx.text("No saved projects found.", color="gray"),
                    ),
                    spacing="2",
                ),
                rx.dialog.close(rx.button("Cancel", variant="soft", margin_top="3")),
            ),
            open=DialogState.open_project_open,
            on_open_change=DialogState.set_open_project_open,
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Rename project"),
                rx.vstack(
                    rx.text("New project name:"),
                    rx.input(
                        placeholder="Project name",
                        value=DialogState.rename_value,
                        on_change=DialogState.set_rename_value,
                    ),
                    rx.hstack(
                        rx.dialog.close(rx.button("Cancel", variant="soft")),
                        rx.dialog.close(
                            rx.button(
                                "Rename",
                                on_click=GraphState.rename_project(DialogState.rename_value),
                                disabled=DialogState.rename_value == "",
                            )
                        ),
                        spacing="3",
                        justify="end",
                    ),
                    spacing="3",
                ),
            ),
            open=DialogState.rename_open,
            on_open_change=DialogState.set_rename_open,
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("New project"),
                rx.vstack(
                    rx.callout.root(
                        rx.callout.text(
                            "Current project «"
                            + GraphState.project_name
                            + "» will be saved automatically."
                        ),
                        color_scheme="blue",
                        size="1",
                    ),
                    rx.text("New project name:"),
                    rx.input(
                        placeholder="my-project",
                        value=DialogState.new_project_name,
                        on_change=DialogState.set_new_project_name,
                    ),
                    rx.hstack(
                        rx.dialog.close(rx.button("Cancel", variant="soft")),
                        rx.dialog.close(
                            rx.button(
                                "Create",
                                on_click=GraphState.new_project(DialogState.new_project_name),
                                disabled=DialogState.new_project_name == "",
                            )
                        ),
                        spacing="3",
                        justify="end",
                    ),
                    spacing="3",
                ),
            ),
            open=DialogState.new_project_open,
            on_open_change=DialogState.set_new_project_open,
        ),
    )


def top_menu() -> rx.Component:
    return rx.hstack(
        rx.cond(
            DialogState.project_list,
            rx.select(
                DialogState.project_list,
                value=GraphState.project_name,
                on_change=GraphState.switch_project,
                on_open_change=DialogState.handle_project_select_open,
                placeholder="Project",
                size="3",
                color_scheme="indigo",
                variant="classic",
            ),
            rx.select(
                [],
                placeholder="No saved projects",
                disabled=True,
                size="3",
                color_scheme="gray",
                variant="classic",
            ),
        ),
        rx.separator(orientation="vertical", size="2"),
        rx.menu.root(
            rx.menu.trigger(
                rx.button("File", variant="solid", size="3", color_scheme="blue")
            ),
            rx.menu.content(
                rx.menu.item("Load data (CSV / Parquet)…", on_click=DialogState.open_create),
                rx.menu.separator(),
                rx.menu.item("Upload project (YAML)…", on_click=DialogState.open_load),
                rx.menu.separator(),
                rx.menu.item("Download project", on_click=DialogState.open_save),
                rx.menu.item("Export pipeline (selected node)…", on_click=GraphState.export_branch_pipeline),
                rx.menu.item("Rename project…", on_click=DialogState.open_rename),
                rx.menu.separator(),
                rx.menu.item("Base schema constructor…", on_click=BaseSchemaState.open_constructor),
                rx.menu.item("Edit schema", on_click=SchemaState.open_schema),
                rx.menu.separator(),
                rx.menu.item("New project…", on_click=DialogState.open_new_project_dialog),
                rx.menu.item("Open project…", on_click=DialogState.open_project_switcher),
                rx.menu.separator(),
                rx.menu.item("Log out", on_click=AuthState.do_logout),
            ),
        ),
        rx.menu.root(
            rx.menu.trigger(
                rx.button("Add", variant="solid", size="3", color_scheme="blue")
            ),
            rx.menu.content(
                rx.menu.sub(
                    rx.menu.sub_trigger("Transformers"),
                    rx.menu.sub_content(
                        rx.foreach(
                            ConfigState.transformer_names,
                            lambda name: rx.menu.item(
                                name,
                                on_click=ConfigState.open_dialog_with_class(name),
                            ),
                        ),
                    ),
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.hstack(
                        rx.icon("cpu", size=14),
                        rx.text("GLM Model"),
                        spacing="2",
                    ),
                    on_click=ModelConfigState.open_for_parent(GraphState.selected_node_id),
                ),
            ),
        ),
        rx.menu.root(
            rx.menu.trigger(
                rx.button("Edit", variant="solid", size="3", color_scheme="blue")
            ),
            rx.menu.content(rx.menu.item("(coming soon)", disabled=True)),
        ),
        rx.menu.root(
            rx.menu.trigger(
                rx.button("View", variant="solid", size="3", color_scheme="blue")
            ),
            rx.menu.content(rx.menu.item("(coming soon)", disabled=True)),
        ),
        _project_dialogs(),
        rx.badge(
            f"v{_APP_VERSION}.{_BUILD}",
            variant="solid",
            color_scheme="indigo",
            size="2",
            margin_left="auto",
        ),
        bg="white",
        border_bottom="1px solid #e5e7eb",
        padding_x="4",
        padding_y="3",
        width="100%",
        spacing="3",
        align="center",
    )
