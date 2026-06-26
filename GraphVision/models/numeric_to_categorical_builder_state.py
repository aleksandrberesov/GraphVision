"""
State for the Numeric → Categorical Builder dialog.

Two non-overlapping groups: ``ordered_features`` and ``unordered_features``.
A column assigned to one group is locked out of the other (the backend rejects
overlap). Off-spec params (max_categories, weight_column, keep_original) are
defaulted and never shown.
"""

from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx


class NumericToCategoricalBuilderState(rx.State):
    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    available_columns: List[str] = []
    ordered_features: List[str] = []
    unordered_features: List[str] = []

    @rx.var
    def can_submit(self) -> bool:
        return bool(self.ordered_features) or bool(self.unordered_features)

    async def _load_numeric_columns(self, parent_vertex_id: str) -> List[str]:
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"
        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_vertex_id)
        if cols_by_type:
            return list(cols_by_type.get("numeric", []))
        return []

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        from .busy_state import BusyState

        yield BusyState.show("Loading columns…")
        cols = await self._load_numeric_columns(parent_vertex_id)
        yield BusyState.hide()

        self.parent_vertex_id = parent_vertex_id
        self.available_columns = cols
        self.ordered_features = []
        self.unordered_features = []
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
        cols = await self._load_numeric_columns(parent_id)
        yield BusyState.hide()

        self.parent_vertex_id = parent_id
        self.available_columns = cols
        self.ordered_features = list(existing_config.get("ordered_features", []) or [])
        self.unordered_features = list(existing_config.get("unordered_features", []) or [])
        self.is_edit_mode = True
        self.vertex_id_editing = vertex_id
        self.is_open = True

    @rx.event
    def close(self):
        self.is_open = False

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    @rx.event
    def toggle_ordered(self, col: str):
        if col in self.unordered_features:
            return  # locked — already unordered
        if col in self.ordered_features:
            self.ordered_features = [c for c in self.ordered_features if c != col]
        else:
            self.ordered_features = self.ordered_features + [col]

    @rx.event
    def toggle_unordered(self, col: str):
        if col in self.ordered_features:
            return  # locked — already ordered
        if col in self.unordered_features:
            self.unordered_features = [c for c in self.unordered_features if c != col]
        else:
            self.unordered_features = self.unordered_features + [col]

    @rx.event
    def select_all_ordered(self):
        # Every column not locked by the unordered group goes to ordered.
        self.ordered_features = [
            c for c in self.available_columns if c not in self.unordered_features
        ]

    @rx.event
    def invert_ordered(self):
        avail = [c for c in self.available_columns if c not in self.unordered_features]
        self.ordered_features = [c for c in avail if c not in self.ordered_features]

    @rx.event
    def select_all_unordered(self):
        self.unordered_features = [
            c for c in self.available_columns if c not in self.ordered_features
        ]

    @rx.event
    def invert_unordered(self):
        avail = [c for c in self.available_columns if c not in self.ordered_features]
        self.unordered_features = [c for c in avail if c not in self.unordered_features]

    @rx.event
    def clear_groups(self):
        self.ordered_features = []
        self.unordered_features = []

    @rx.event
    async def submit(self):
        if not self.ordered_features and not self.unordered_features:
            yield rx.toast.error("Assign at least one column.")
            return

        config: Dict[str, Any] = {
            "ordered_features": list(self.ordered_features),
            "unordered_features": list(self.unordered_features),
        }

        from .graph import GraphState
        graph_state = await self.get_state(GraphState)
        self.is_open = False

        if self.is_edit_mode:
            vertex_id = self.vertex_id_editing
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.apply_config_edit(vertex_id, "GLMNumericToCategoricalTransformation", config)
        else:
            if self.parent_vertex_id:
                yield graph_state._select_node(self.parent_vertex_id)
            yield GraphState.add_transformation_node("GLMNumericToCategoricalTransformation", config)
