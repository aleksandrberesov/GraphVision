from __future__ import annotations

from typing import List

import reflex as rx


class DataPreviewState(rx.State):
    is_open: bool = False
    columns: List[str] = []
    rows: List[List[str]] = []
    total_rows: int = 0

    @rx.var
    def row_count_label(self) -> str:
        return f"Showing {len(self.rows)} of {self.total_rows} rows"

    @rx.event
    async def open_preview(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        vertex_id = graph_state.selected_node_id
        if not vertex_id:
            return

        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        yield BusyState.show("Loading data preview...")
        result = pipeline_hooks.get_data_preview(session_id, vertex_id, 100)
        yield BusyState.hide()
        if result is None:
            yield rx.toast.error("No data available — load a dataset first.")
            return
        self.columns = result["columns"]
        self.rows = result["rows"]
        self.total_rows = result["total_rows"]
        self.is_open = True

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value
