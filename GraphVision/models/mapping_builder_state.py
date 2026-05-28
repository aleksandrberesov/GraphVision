"""
State for the Category Mapping Builder dialog.

Lets the user pick categorical columns, then assigns a group label to
every unique value in each column. At submit it builds the 'mappings'
dict required by GLMCategoryMappingTransformation.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import reflex as rx


class MappingBuilderState(rx.State):
    """Dialog state for the visual category mapping builder."""

    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    # Categorical columns available at the parent vertex
    available_columns: List[str] = []
    # Columns the user has chosen to map
    selected_features: List[str] = []

    # Active column being edited in the mapping table
    active_column: str = ""

    # Rows for the active column: [{"value": str, "group": str}, ...]
    active_rows: List[Dict[str, str]] = []

    # Persisted mapping per column: {col: JSON string of {val: group}}
    saved_mappings: Dict[str, str] = {}

    unknown_strategy: str = "unknown"
    keep_original: bool = True

    @rx.var
    def can_submit(self) -> bool:
        return bool(self.selected_features)

    # ------------------------------------------------------------------ #
    # Open / close                                                         #
    # ------------------------------------------------------------------ #

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        """Open in add-mode for the given parent vertex."""
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .busy_state import BusyState
        from .graph import GraphState

        yield BusyState.show("Loading columns…")
        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"

        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_vertex_id)
        yield BusyState.hide()

        cat_cols: List[str] = []
        if cols_by_type:
            cat_cols = (
                cols_by_type.get("categorical", [])
                + cols_by_type.get("ordered_categorical", [])
            )

        self.parent_vertex_id = parent_vertex_id
        self.available_columns = cat_cols
        self.selected_features = []
        self.active_column = ""
        self.active_rows = []
        self.saved_mappings = {}
        self.unknown_strategy = "unknown"
        self.keep_original = True
        self.is_edit_mode = False
        self.vertex_id_editing = ""
        self.is_open = True

    @rx.event
    async def open_edit_dialog(self, vertex_id: str, existing_config: Dict[str, Any]):
        """Open in edit-mode pre-filled with existing config."""
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .busy_state import BusyState
        from .graph import GraphState

        yield BusyState.show("Loading columns…")
        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"

        parent_id = next(
            (e["source"] for e in graph_state.edges if e["target"] == vertex_id),
            None,
        ) or vertex_id
        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_id)
        yield BusyState.hide()

        cat_cols: List[str] = []
        if cols_by_type:
            cat_cols = (
                cols_by_type.get("categorical", [])
                + cols_by_type.get("ordered_categorical", [])
            )

        existing_mappings: Dict[str, Dict[str, str]] = existing_config.get("mappings", {})
        saved: Dict[str, str] = {
            col: json.dumps(val_map)
            for col, val_map in existing_mappings.items()
        }

        self.parent_vertex_id = parent_id
        self.available_columns = cat_cols
        self.selected_features = list(existing_mappings.keys())
        self.active_column = ""
        self.active_rows = []
        self.saved_mappings = saved
        self.unknown_strategy = existing_config.get("unknown_strategy", "unknown")
        self.keep_original = existing_config.get("keep_original", True)
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
    # Column selection + value loading                                     #
    # ------------------------------------------------------------------ #

    def _flush_active_rows(self):
        """Save active_rows into saved_mappings before switching column."""
        if self.active_column and self.active_rows:
            val_map = {r["value"]: r["group"] for r in self.active_rows}
            self.saved_mappings = {**self.saved_mappings, self.active_column: json.dumps(val_map)}

    @rx.event
    async def toggle_feature(self, col: str):
        """Add or remove a column from the mapping selection."""
        self._flush_active_rows()
        if col in self.selected_features:
            self.selected_features = [c for c in self.selected_features if c != col]
            if self.active_column == col:
                self.active_column = ""
                self.active_rows = []
        else:
            self.selected_features = self.selected_features + [col]
            yield MappingBuilderState.set_active_column(col)

    @rx.event
    async def set_active_column(self, col: str):
        """Switch the column being edited; loads unique values on first visit."""
        if col == self.active_column:
            return
        self._flush_active_rows()
        self.active_column = col

        # Restore saved rows if already visited
        if col in self.saved_mappings:
            val_map = json.loads(self.saved_mappings[col])
            self.active_rows = [{"value": v, "group": g} for v, g in val_map.items()]
            return

        # Load unique values from backend
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"

        unique_vals: List[str] = pipeline_hooks.get_unique_column_values(
            session_id, self.parent_vertex_id, col
        )
        self.active_rows = [{"value": v, "group": v} for v in unique_vals]

    # ------------------------------------------------------------------ #
    # Editing                                                              #
    # ------------------------------------------------------------------ #

    @rx.event
    def update_row_group(self, value: str, group: str):
        self.active_rows = [
            {**r, "group": group} if r["value"] == value else r
            for r in self.active_rows
        ]

    @rx.event
    def set_unknown_strategy(self, value: str):
        self.unknown_strategy = value

    @rx.event
    def set_keep_original(self, value: str):
        self.keep_original = value.lower() in ("true", "1", "yes")

    # ------------------------------------------------------------------ #
    # Submit                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def submit(self):
        if not self.selected_features:
            yield rx.toast.error("Select at least one column to map.")
            return

        self._flush_active_rows()

        mappings: Dict[str, Dict[str, str]] = {}
        for col in self.selected_features:
            if col in self.saved_mappings:
                mappings[col] = json.loads(self.saved_mappings[col])
            else:
                mappings[col] = {}

        config: Dict[str, Any] = {
            "features_to_transform": list(self.selected_features),
            "mappings": mappings,
            "unknown_strategy": self.unknown_strategy,
            "keep_original": self.keep_original,
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
                "GLMCategoryMappingTransformation",
                config,
            )
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.refresh_statuses_from_pipeline()
        else:
            if self.parent_vertex_id:
                yield graph_state._select_node(self.parent_vertex_id)
            yield GraphState.add_transformation_node("GLMCategoryMappingTransformation", config)
