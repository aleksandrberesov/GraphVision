import reflex as rx

from ..models import DialogState
from ..models.auth_state import AuthState
from ..models.config_state import ConfigState
from ..models.schema_state import SchemaState


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
        bg="white",
        border_bottom="1px solid #e5e7eb",
        padding_x="4",
        padding_y="3",
        width="100%",
        spacing="3",
        align="center",
    )
