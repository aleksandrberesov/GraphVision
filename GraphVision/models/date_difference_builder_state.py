"""
State for the Date Difference Builder dialog.

The user picks a difference type (days / months / years) and a From / To
column pair, then "+ Add" stacks that onto a per-pair entry. At submit it
builds the ``differences`` dict required by GLMDateDifferenceTransformation:

    {"<from>__to__<to>": {"from": <from>, "to": <to>, "features": ["days", ...]}}

``features_to_transform`` is the union of every From/To column referenced.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import reflex as rx

_DIFF_TYPES = ["days", "months", "years"]


class DateDifferenceBuilderState(rx.State):
    """Dialog state for the visual date-difference builder."""

    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    available_columns: List[str] = []

    # Current selection
    diff_type: str = "days"
    from_col: str = ""
    to_col: str = ""

    # Accumulated: {config_name: JSON string of {"from","to","features"}}
    entries: Dict[str, str] = {}

    @rx.var
    def diff_types(self) -> List[str]:
        return _DIFF_TYPES

    @rx.var
    def can_submit(self) -> bool:
        return bool(self.entries)

    @rx.var
    def entry_rows(self) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for name, cfg_json in self.entries.items():
            try:
                cfg = json.loads(cfg_json)
            except (ValueError, TypeError):
                cfg = {}
            rows.append({
                "name": name,
                "label": f"{cfg.get('from', '?')} → {cfg.get('to', '?')}",
                "features": ", ".join(cfg.get("features", [])),
            })
        return rows

    # ------------------------------------------------------------------ #
    # Open / close                                                         #
    # ------------------------------------------------------------------ #

    async def _load_all_columns(self, parent_vertex_id: str) -> List[str]:
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"
        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_vertex_id)
        cols: List[str] = []
        if cols_by_type:
            for col_list in cols_by_type.values():
                cols.extend(col_list)
        return cols

    def _reset_current(self):
        self.diff_type = "days"
        self.from_col = ""
        self.to_col = ""

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        from .busy_state import BusyState

        yield BusyState.show("Loading columns…")
        cols = await self._load_all_columns(parent_vertex_id)
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
        cols = await self._load_all_columns(parent_id)
        yield BusyState.hide()

        existing: Dict[str, Dict[str, Any]] = existing_config.get("differences", {})

        self.parent_vertex_id = parent_id
        self.available_columns = cols
        self.entries = {name: json.dumps(cfg) for name, cfg in existing.items()}
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

    # ------------------------------------------------------------------ #
    # Current selection                                                    #
    # ------------------------------------------------------------------ #

    @rx.event
    def set_diff_type(self, value: str):
        self.diff_type = value

    @rx.event
    def set_from_col(self, value: str):
        self.from_col = value

    @rx.event
    def set_to_col(self, value: str):
        self.to_col = value

    @rx.event
    def add_current(self):
        if not self.from_col or not self.to_col:
            yield rx.toast.error("Pick both a From and a To column.")
            return
        if self.from_col == self.to_col:
            yield rx.toast.error("From and To must be different columns.")
            return

        name = f"{self.from_col}__to__{self.to_col}"
        new_entries = dict(self.entries)
        if name in new_entries:
            try:
                cfg = json.loads(new_entries[name])
            except (ValueError, TypeError):
                cfg = {"from": self.from_col, "to": self.to_col, "features": []}
        else:
            cfg = {"from": self.from_col, "to": self.to_col, "features": []}

        feats = cfg.get("features", [])
        if self.diff_type not in feats:
            feats.append(self.diff_type)
        cfg["features"] = feats
        new_entries[name] = json.dumps(cfg)
        self.entries = new_entries
        self._reset_current()

    @rx.event
    def remove_entry(self, name: str):
        self.entries = {k: v for k, v in self.entries.items() if k != name}

    @rx.event
    def clear_entries(self):
        self.entries = {}

    # ------------------------------------------------------------------ #
    # Submit                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def submit(self):
        if not self.entries:
            yield rx.toast.error("Add at least one date difference.")
            return

        differences: Dict[str, Dict[str, Any]] = {}
        used_cols: List[str] = []
        for name, cfg_json in self.entries.items():
            try:
                cfg = json.loads(cfg_json)
            except (ValueError, TypeError):
                continue
            differences[name] = cfg
            for key in ("from", "to"):
                col = cfg.get(key)
                if col and col not in used_cols:
                    used_cols.append(col)

        config: Dict[str, Any] = {
            "features_to_transform": used_cols,
            "differences": differences,
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
                session_id,
                self.vertex_id_editing,
                "GLMDateDifferenceTransformation",
                config,
            )
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.refresh_statuses_from_pipeline()
        else:
            if self.parent_vertex_id:
                yield graph_state._select_node(self.parent_vertex_id)
            yield GraphState.add_transformation_node("GLMDateDifferenceTransformation", config)
