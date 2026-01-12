import reflex as rx

from rxconfig import config

from .pages import (
    main_page,
)

app = rx.App(theme=rx.theme(accent_color="green"))

app.add_page(main_page, route="/", title="Main")