"""
State for the Binning Builder dialog.

Per-column binning method(s) + ``n_bins``. The method strings are the exact
Cyrillic values the backend BinningTransformer matches on
(квантили / экспо_квантили / интервалы / лог_интервалы). Accumulated, then
split into the dicts GLMBinningTransformation expects:

    methods = {col: [method, ...]}
    n_bins  = {col: n}

``weight_column`` is a SCHEMA_PARAM (auto-filled by the bridge) and never shown.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import reflex as rx

# value (backend string) → display label
_METHODS = [
    {"value": "квантили", "label": "Quantiles (квантили)"},
    {"value": "экспо_квантили", "label": "Expo-quantiles (экспо_квантили)"},
    {"value": "интервалы", "label": "Intervals (интервалы)"},
    {"value": "лог_интервалы", "label": "Log-intervals (лог_интервалы)"},
]
_METHOD_VALUES = [m["value"] for m in _METHODS]


class BinningBuilderState(rx.State):
    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    available_columns: List[str] = []

    method: str = "квантили"
    n_bins: str = "5"
    selected_features: List[str] = []

    # col -> JSON {"methods": [str], "n_bins": int}
    entries: Dict[str, str] = {}

    @rx.var
    def method_labels(self) -> List[str]:
        return [m["label"] for m in _METHODS]

    @rx.var
    def method_label(self) -> str:
        for m in _METHODS:
            if m["value"] == self.method:
                return m["label"]
        return self.method

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
                "summary": f"{', '.join(cfg.get('methods', []))} · n_bins={cfg.get('n_bins', '?')}",
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
        self.method = "квантили"
        self.n_bins = "5"
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

        methods: Dict[str, List[str]] = existing_config.get("methods", {}) or {}
        n_bins: Dict[str, int] = existing_config.get("n_bins", {}) or {}
        entries: Dict[str, str] = {}
        for col, mlist in methods.items():
            entries[col] = json.dumps({"methods": list(mlist), "n_bins": n_bins.get(col, 5)})

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
    def set_method(self, label: str):
        for m in _METHODS:
            if m["label"] == label:
                self.method = m["value"]
                return
        if label in _METHOD_VALUES:
            self.method = label

    @rx.event
    def set_n_bins(self, value: str):
        self.n_bins = value

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
        n = self._parse_int(self.n_bins)
        if n is None or n < 2:
            yield rx.toast.error("n_bins must be an integer ≥ 2.")
            return

        new_entries = dict(self.entries)
        for col in self.selected_features:
            if col in new_entries:
                try:
                    cfg = json.loads(new_entries[col])
                except (ValueError, TypeError):
                    cfg = {"methods": [], "n_bins": n}
            else:
                cfg = {"methods": [], "n_bins": n}
            methods = cfg.get("methods", [])
            if self.method not in methods:
                methods.append(self.method)
            cfg["methods"] = methods
            cfg["n_bins"] = n
            new_entries[col] = json.dumps(cfg)
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

        methods: Dict[str, List[str]] = {}
        n_bins: Dict[str, int] = {}
        for col, cfg_json in self.entries.items():
            try:
                cfg = json.loads(cfg_json)
            except (ValueError, TypeError):
                continue
            methods[col] = cfg.get("methods", [])
            n_bins[col] = cfg.get("n_bins", 5)

        config: Dict[str, Any] = {
            "features_to_transform": list(methods.keys()),
            "methods": methods,
            "n_bins": n_bins,
            "keep_original": True,
        }

        from .graph import GraphState
        graph_state = await self.get_state(GraphState)
        self.is_open = False

        if self.is_edit_mode:
            vertex_id = self.vertex_id_editing
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.apply_config_edit(vertex_id, "GLMBinningTransformation", config)
        else:
            if self.parent_vertex_id:
                yield graph_state._select_node(self.parent_vertex_id)
            yield GraphState.add_transformation_node("GLMBinningTransformation", config)
