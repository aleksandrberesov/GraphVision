"""
State for the Feature Pair Builder dialog.

GLMFeaturePairTransformation produces the cartesian product of two
non-overlapping column groups (first_group × second_group). The user assigns
columns to "First group" and "Second group"; a column placed in one group is
locked out of the other (the backend rejects overlapping groups).

Off-spec params (separator, validate_ordered, keep_original) are defaulted and
never shown.
"""

from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx


class FeaturePairBuilderState(rx.State):
    """Dialog state for the visual feature-pair builder."""

    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    available_columns: List[str] = []
    first_group: List[str] = []
    second_group: List[str] = []

    @rx.var
    def can_submit(self) -> bool:
        return bool(self.first_group) and bool(self.second_group)

    @rx.var
    def pair_count(self) -> int:
        return len(self.first_group) * len(self.second_group)

    # ------------------------------------------------------------------ #
    # Open / close                                                         #
    # ------------------------------------------------------------------ #

    async def _load_categorical_columns(self, parent_vertex_id: str) -> List[str]:
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"
        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_vertex_id)
        if not cols_by_type:
            return []
        cols = (
            cols_by_type.get("categorical", [])
            + cols_by_type.get("ordered_categorical", [])
        )
        # Fall back to every column if the schema has no categoricals yet.
        if not cols:
            for col_list in cols_by_type.values():
                cols.extend(col_list)
        return cols

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        from .busy_state import BusyState

        yield BusyState.show("Loading columns…")
        cols = await self._load_categorical_columns(parent_vertex_id)
        yield BusyState.hide()

        self.parent_vertex_id = parent_vertex_id
        self.available_columns = cols
        self.first_group = []
        self.second_group = []
        self.is_edit_mode = False
        self.vertex_id_editing = ""
        self.is_open = True

    @rx.event
    async def open_edit_dialog(self, vertex_id: str, existing_config: Dict[str, Any]):
        from .busy_state import BusyState
        from .graph import GraphState

        yield BusyState.show("Loading columns…")
        graph_state = await self.get_state(GraphState)
        parent_id = next(
            (e["source"] for e in graph_state.edges if e["target"] == vertex_id),
            None,
        ) or vertex_id
        cols = await self._load_categorical_columns(parent_id)
        yield BusyState.hide()

        self.parent_vertex_id = parent_id
        self.available_columns = cols
        self.first_group = list(existing_config.get("first_group", []) or [])
        self.second_group = list(existing_config.get("second_group", []) or [])
        self.is_edit_mode = True
        self.vertex_id_editing = vertex_id
        self.is_open = True

    @rx.event
    def close(self):
        self.is_open = False

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    # ------------------------------------------------------------------ #
    # Group assignment (a column lives in at most one group)               #
    # ------------------------------------------------------------------ #

    @rx.event
    def toggle_first(self, col: str):
        if col in self.second_group:
            return  # locked — already in the other group
        if col in self.first_group:
            self.first_group = [c for c in self.first_group if c != col]
        else:
            self.first_group = self.first_group + [col]

    @rx.event
    def toggle_second(self, col: str):
        if col in self.first_group:
            return  # locked — already in the other group
        if col in self.second_group:
            self.second_group = [c for c in self.second_group if c != col]
        else:
            self.second_group = self.second_group + [col]

    @rx.event
    def clear_groups(self):
        self.first_group = []
        self.second_group = []

    # ------------------------------------------------------------------ #
    # Submit                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def submit(self):
        if not self.first_group or not self.second_group:
            yield rx.toast.error("Both groups need at least one column.")
            return

        config: Dict[str, Any] = {
            "first_group": list(self.first_group),
            "second_group": list(self.second_group),
        }

        from .graph import GraphState
        graph_state = await self.get_state(GraphState)
        self.is_open = False

        if self.is_edit_mode:
            from .auth_state import AuthState
            from . import pipeline_hooks
            session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
            pipeline_hooks.update_transformation_config(
                session_id,
                self.vertex_id_editing,
                "GLMFeaturePairTransformation",
                config,
            )
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.refresh_statuses_from_pipeline()
        else:
            if self.parent_vertex_id:
                yield graph_state._select_node(self.parent_vertex_id)
            yield GraphState.add_transformation_node("GLMFeaturePairTransformation", config)
