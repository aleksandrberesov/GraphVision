"""
State for the Cyclic Features Builder dialog.

Per-column ``period`` + ``num_pairs``, accumulated then split into the two
dicts GLMCyclicTransformation expects:

    periods   = {col: period}
    num_pairs = {col: num_pairs}
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import reflex as rx


class CyclicBuilderState(rx.State):
    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    available_columns: List[str] = []

    period: str = ""
    num_pairs: str = "2"
    selected_features: List[str] = []

    # col -> JSON {"period": int, "num_pairs": int}
    entries: Dict[str, str] = {}

    @rx.var
    def can_submit(self) -> bool:
        return bool(self.entries)

    @rx.var
    def entry_rows(self) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for col, cfg_json in self.entries.items():
            try:
                cfg = json.loads(cfg_json)
            except (ValueError, TypeError):
                cfg = {}
            rows.append({
                "col": col,
                "summary": f"period={cfg.get('period', '?')}, pairs={cfg.get('num_pairs', '?')}",
            })
        return rows

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

    def _reset_current(self):
        self.period = ""
        self.num_pairs = "2"
        self.selected_features = []

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        from .busy_state import BusyState

        yield BusyState.show("Loading columns…")
        cols = await self._load_numeric_columns(parent_vertex_id)
        yield BusyState.hide()

        self.parent_vertex_id = parent_vertex_id
        self.available_columns = cols
        self.entries = {}
        self._reset_current()
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

        periods: Dict[str, int] = existing_config.get("periods", {}) or {}
        np_cfg = existing_config.get("num_pairs", 2)
        entries: Dict[str, str] = {}
        for col, period in periods.items():
            if isinstance(np_cfg, dict):
                n = np_cfg.get(col, 2)
            else:
                n = np_cfg
            entries[col] = json.dumps({"period": period, "num_pairs": n})

        self.parent_vertex_id = parent_id
        self.available_columns = cols
        self.entries = entries
        self._reset_current()
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
    def set_period(self, value: str):
        self.period = value

    @rx.event
    def set_num_pairs(self, value: str):
        self.num_pairs = value

    @rx.event
    def toggle_feature(self, col: str):
        if col in self.selected_features:
            self.selected_features = [c for c in self.selected_features if c != col]
        else:
            self.selected_features = self.selected_features + [col]

    @staticmethod
    def _parse_int(s: str):
        try:
            return int(float(s.strip()))
        except (ValueError, AttributeError):
            return None

    @rx.event
    def add_current(self):
        if not self.selected_features:
            yield rx.toast.error("Select at least one column.")
            return
        period = self._parse_int(self.period)
        n_pairs = self._parse_int(self.num_pairs)
        if period is None or period <= 0:
            yield rx.toast.error("Period must be a positive integer.")
            return
        if n_pairs is None or n_pairs <= 0:
            yield rx.toast.error("Num pairs must be a positive integer.")
            return

        new_entries = dict(self.entries)
        for col in self.selected_features:
            new_entries[col] = json.dumps({"period": period, "num_pairs": n_pairs})
        self.entries = new_entries
        self._reset_current()

    @rx.event
    def remove_entry(self, col: str):
        self.entries = {k: v for k, v in self.entries.items() if k != col}

    @rx.event
    def clear_entries(self):
        self.entries = {}

    @rx.event
    async def submit(self):
        if not self.entries:
            yield rx.toast.error("Configure at least one column.")
            return

        periods: Dict[str, int] = {}
        num_pairs: Dict[str, int] = {}
        for col, cfg_json in self.entries.items():
            try:
                cfg = json.loads(cfg_json)
            except (ValueError, TypeError):
                continue
            periods[col] = cfg["period"]
            num_pairs[col] = cfg["num_pairs"]

        config: Dict[str, Any] = {
            "features_to_transform": list(periods.keys()),
            "periods": periods,
            "num_pairs": num_pairs,
            "keep_original": True,
        }

        from .graph import GraphState
        graph_state = await self.get_state(GraphState)
        self.is_open = False

        if self.is_edit_mode:
            from .auth_state import AuthState
            from . import pipeline_hooks
            session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
            pipeline_hooks.update_transformation_config(
                session_id, self.vertex_id_editing, "GLMCyclicTransformation", config
            )
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.refresh_statuses_from_pipeline()
        else:
            if self.parent_vertex_id:
                yield graph_state._select_node(self.parent_vertex_id)
            yield GraphState.add_transformation_node("GLMCyclicTransformation", config)
