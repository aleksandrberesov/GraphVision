import reflex as rx

from ..models import DialogState
from ..models.auth_state import AuthState
from ..models.config_state import ConfigState
from ..models.graph import GraphState
from ..models.schema_state import SchemaState


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
                        DialogState.project_list.length() == 0,
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
                rx.dialog.title("New project"),
                rx.vstack(
                    rx.text("Project name:"),
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
        rx.menu.root(
            rx.menu.trigger(
                rx.button("File", variant="solid", size="3", color_scheme="blue")
            ),
            rx.menu.content(
                rx.menu.item("New graph", on_click=DialogState.open_create),
                rx.menu.separator(),
                rx.menu.item("Upload graph", on_click=DialogState.open_load),
                rx.menu.separator(),
                rx.menu.item("Save graph", on_click=DialogState.open_save),
                rx.menu.separator(),
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
                rx.menu.item("Models", disabled=True),
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
        bg="white",
        border_bottom="1px solid #e5e7eb",
        padding_x="4",
        padding_y="3",
        width="100%",
        spacing="3",
        align="center",
    )
