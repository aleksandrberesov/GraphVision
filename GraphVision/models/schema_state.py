from __future__ import annotations

from typing import Dict, List

import reflex as rx


class SchemaState(rx.State):
    is_open: bool = False
    rows: List[Dict[str, str]] = []

    @rx.event
    async def open_schema(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .busy_state import BusyState

        session_id = (await self.get_state(AuthState)).user_id
        if not pipeline_hooks.get_pipeline(session_id):
            return
        yield BusyState.show("Loading schema...")
        rows = pipeline_hooks.get_schema(session_id)
        yield BusyState.hide()
        if rows is not None:
            self.rows = rows
            self.is_open = True

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    @rx.event
    def update_row_type(self, name: str, col_type: str):
        self.rows = [
            {**r, "type": col_type} if r["name"] == name else r
            for r in self.rows
        ]

    @rx.event
    async def save_schema(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .busy_state import BusyState

        session_id = (await self.get_state(AuthState)).user_id
        yield BusyState.show("Saving schema...")
        schema_dict = {r["name"]: r["type"] for r in self.rows}
        pipeline_hooks.update_schema(session_id, schema_dict)
        yield BusyState.hide()
        self.is_open = False
