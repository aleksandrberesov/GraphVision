import importlib
import os

import reflex as rx

from rxconfig import config

from .pages import (
    main_page,
)

_hooks_module = os.environ.get("GRAPHVISION_PIPELINE_HOOKS")
if _hooks_module:
    importlib.import_module(_hooks_module).register()

_accent_color = os.environ.get("GRAPHVISION_ACCENT_COLOR", "green")
_title = os.environ.get("GRAPHVISION_TITLE", "GraphVision")

app = rx.App(theme=rx.theme(accent_color=_accent_color))  # type: ignore[arg-type]

app.add_page(main_page, route="/", title=_title)