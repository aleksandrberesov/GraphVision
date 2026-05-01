import importlib
import os

import reflex as rx
from reflex_local_auth import require_login

from rxconfig import config

from .models.graph import GraphState
from .pages import (
    login_page,
    main_page,
    register_page,
)

_hooks_module = os.environ.get("GRAPHVISION_PIPELINE_HOOKS")
if _hooks_module:
    importlib.import_module(_hooks_module).register()

_accent_color = os.environ.get("GRAPHVISION_ACCENT_COLOR", "green")
_title = os.environ.get("GRAPHVISION_TITLE", "GraphVision")

app = rx.App(theme=rx.theme(accent_color=_accent_color))  # type: ignore[arg-type]

app.add_page(require_login(main_page), route="/", title=_title, on_load=GraphState.restore_session)
app.add_page(login_page, route="/login", title="Login")
app.add_page(register_page, route="/register", title="Register")