"""
State for the Target Encoding Builder dialog.

Pick categorical features to encode, one or more aggregations, and exactly one
target. Builds the config for GLMTargetTransformation:

    {features_to_encode, aggregations, target_columns: [target]}

``weight_column`` is a SCHEMA_PARAM (auto-filled from the schema's exposure) and
never shown; ``target_columns`` is provided here explicitly (overrides autofill).
"""

from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx

_AGGREGATIONS = ["mean", "sd", "sd_mean", "count", "w_count"]


class TargetBuilderState(rx.State):
    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    categorical_columns: List[str] = []
    all_columns: List[str] = []
    numeric_columns: List[str] = []   # numeric-dtype cols to "orient on" (incl. target)

    selected_features: List[str] = []
    selected_aggs: List[str] = []
    target_col: str = ""

    # Accumulated tasks (add-mode only): each is a JSON target-encoding config.
    # On Apply, one chained Target node is created per task (the backend wrapper
    # is one flat config, so heterogeneous tasks = multiple nodes).
    tasks: List[str] = []

    @rx.var
    def aggregation_choices(self) -> List[str]:
        return _AGGREGATIONS

    @rx.var
    def current_complete(self) -> bool:
        return bool(self.selected_features) and bool(self.selected_aggs) and bool(self.target_col)

    @rx.var
    def can_submit(self) -> bool:
        return bool(self.tasks) or self.current_complete

    @rx.var
    def task_rows(self) -> List[Dict[str, str]]:
        import json
        rows: List[Dict[str, str]] = []
        for i, t in enumerate(self.tasks):
            try:
                cfg = json.loads(t)
            except (ValueError, TypeError):
                cfg = {}
            feats = ", ".join(cfg.get("features_to_encode", []))
            aggs = ", ".join(cfg.get("aggregations", []))
            tgt = ", ".join(cfg.get("target_columns", []))
            rows.append({"idx": str(i), "label": f"[{feats}] · {aggs} → {tgt}"})
        return rows

    async def _load_columns(self, parent_vertex_id: str):
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"
        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_vertex_id)
        cat: List[str] = []
        allc: List[str] = []
        if cols_by_type:
            cat = (
                cols_by_type.get("categorical", [])
                + cols_by_type.get("ordered_categorical", [])
            )
            for col_list in cols_by_type.values():
                allc.extend(col_list)
            if not cat:
                cat = list(allc)
        # Numeric-dtype columns (incl. the target) to orient the encoding on.
        num = pipeline_hooks.get_numeric_columns(session_id, parent_vertex_id) or []
        return cat, allc, num

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        from .busy_state import BusyState

        yield BusyState.show("Loading columns…")
        cat, allc, num = await self._load_columns(parent_vertex_id)
        yield BusyState.hide()

        self.parent_vertex_id = parent_vertex_id
        self.categorical_columns = cat
        self.all_columns = allc
        self.numeric_columns = num
        self.selected_features = []
        self.selected_aggs = []
        self.target_col = ""
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
        cat, allc, num = await self._load_columns(parent_id)
        yield BusyState.hide()

        targets = existing_config.get("target_columns", []) or []

        self.parent_vertex_id = parent_id
        self.categorical_columns = cat
        self.all_columns = allc
        self.numeric_columns = num
        self.selected_features = list(existing_config.get("features_to_encode", []) or [])
        self.selected_aggs = list(existing_config.get("aggregations", []) or [])
        self.target_col = targets[0] if targets else ""
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

    @rx.event
    def toggle_feature(self, col: str):
        if col in self.selected_features:
            self.selected_features = [c for c in self.selected_features if c != col]
        else:
            self.selected_features = self.selected_features + [col]

    @rx.event
    def toggle_agg(self, agg: str):
        if agg in self.selected_aggs:
            self.selected_aggs = [a for a in self.selected_aggs if a != agg]
        else:
            self.selected_aggs = self.selected_aggs + [agg]

    @rx.event
    def set_target_col(self, value: str):
        self.target_col = value

    def _current_config(self) -> Dict[str, Any]:
        return {
            "features_to_encode": list(self.selected_features),
            "aggregations": list(self.selected_aggs),
            "target_columns": [self.target_col],
        }

    @rx.event
    def add_task(self):
        import json
        if not self.current_complete:
            yield rx.toast.error("Pick feature(s), aggregation(s) and a target first.")
            return
        self.tasks = self.tasks + [json.dumps(self._current_config())]
        self.selected_features = []
        self.selected_aggs = []
        self.target_col = ""

    @rx.event
    def remove_task(self, idx: int):
        self.tasks = [t for i, t in enumerate(self.tasks) if i != idx]

    @rx.event
    def clear_tasks(self):
        self.tasks = []

    @rx.event
    async def submit(self):
        import json
        from .graph import GraphState
        graph_state = await self.get_state(GraphState)

        # Edit mode is always single-config — update the existing node.
        if self.is_edit_mode:
            if not self.current_complete:
                yield rx.toast.error("Pick feature(s), aggregation(s) and a target.")
                return
            self.is_open = False
            vertex_id = self.vertex_id_editing
            config = self._current_config()
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.apply_config_edit(vertex_id, "GLMTargetTransformation", config)
            return

        # Add mode: accumulated tasks + the current selection (if complete).
        configs: List[Dict[str, Any]] = []
        for t in self.tasks:
            try:
                configs.append(json.loads(t))
            except (ValueError, TypeError):
                continue
        if self.current_complete:
            configs.append(self._current_config())
        if not configs:
            yield rx.toast.error("Add at least one encoding task.")
            return

        self.is_open = False
        if self.parent_vertex_id:
            yield graph_state._select_node(self.parent_vertex_id)
        for cfg in configs:
            yield GraphState.add_transformation_node("GLMTargetTransformation", cfg)
