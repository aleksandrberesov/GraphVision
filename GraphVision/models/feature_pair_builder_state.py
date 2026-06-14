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

    # Accumulated tasks (add-mode only): each is a JSON {"first_group","second_group"}.
    # On Apply, one chained FeaturePair node is created per task — the backend
    # wrapper is a single cartesian product, so multiple group-pairs = multiple nodes.
    tasks: List[str] = []

    @rx.var
    def current_complete(self) -> bool:
        return bool(self.first_group) and bool(self.second_group)

    @rx.var
    def can_submit(self) -> bool:
        # Submit if there's at least one accumulated task or a complete current pair.
        return bool(self.tasks) or self.current_complete

    @rx.var
    def pair_count(self) -> int:
        return len(self.first_group) * len(self.second_group)

    @rx.var
    def task_rows(self) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        import json
        for i, t in enumerate(self.tasks):
            try:
                cfg = json.loads(t)
            except (ValueError, TypeError):
                cfg = {}
            fg = ", ".join(cfg.get("first_group", []))
            sg = ", ".join(cfg.get("second_group", []))
            rows.append({"idx": str(i), "label": f"[{fg}] × [{sg}]"})
        return rows

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
        self.tasks = []
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
        self.tasks = []  # accumulate is add-mode only
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
    # Accumulate (add-mode only)                                            #
    # ------------------------------------------------------------------ #

    @rx.event
    def add_task(self):
        import json
        if not self.first_group or not self.second_group:
            yield rx.toast.error("Both groups need at least one column.")
            return
        self.tasks = self.tasks + [json.dumps({
            "first_group": list(self.first_group),
            "second_group": list(self.second_group),
        })]
        self.first_group = []
        self.second_group = []

    @rx.event
    def remove_task(self, idx: int):
        self.tasks = [t for i, t in enumerate(self.tasks) if i != idx]

    @rx.event
    def clear_tasks(self):
        self.tasks = []

    # ------------------------------------------------------------------ #
    # Submit                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def submit(self):
        import json
        from .graph import GraphState
        graph_state = await self.get_state(GraphState)

        # Edit mode is always single-config — update the existing node.
        if self.is_edit_mode:
            if not self.first_group or not self.second_group:
                yield rx.toast.error("Both groups need at least one column.")
                return
            config = {"first_group": list(self.first_group), "second_group": list(self.second_group)}
            from .auth_state import AuthState
            from . import pipeline_hooks
            session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
            self.is_open = False
            pipeline_hooks.update_transformation_config(
                session_id, self.vertex_id_editing, "GLMFeaturePairTransformation", config
            )
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.refresh_statuses_from_pipeline()
            return

        # Add mode: gather accumulated tasks + the current pair (if complete).
        configs: List[Dict[str, Any]] = []
        for t in self.tasks:
            try:
                configs.append(json.loads(t))
            except (ValueError, TypeError):
                continue
        if self.first_group and self.second_group:
            configs.append({
                "first_group": list(self.first_group),
                "second_group": list(self.second_group),
            })
        if not configs:
            yield rx.toast.error("Add at least one group pair.")
            return

        self.is_open = False
        # One chained FeaturePair node per task (add_transformation_node selects the
        # new node, so each subsequent add chains onto it).
        if self.parent_vertex_id:
            yield graph_state._select_node(self.parent_vertex_id)
        for cfg in configs:
            yield GraphState.add_transformation_node("GLMFeaturePairTransformation", cfg)
