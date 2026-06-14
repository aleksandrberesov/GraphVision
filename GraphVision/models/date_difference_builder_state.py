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

    # Current selection (multi-select, mirroring the notebook)
    use_days: bool = False
    use_months: bool = False
    use_years: bool = False
    from_cols: List[str] = []
    to_cols: List[str] = []
    # TO can be column(s) *or* a fixed date string (e.g. "2025-01"); the backend
    # treats config["to"] as a fixed date when it isn't one of the columns.
    to_is_fixed: bool = False
    to_fixed_value: str = ""

    # Accumulated: {config_name: JSON string of {"from","to","features","to_fixed"}}
    entries: Dict[str, str] = {}

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
            to_label = f"{cfg.get('to', '?')}"
            if cfg.get("to_fixed"):
                to_label += " (fixed)"
            rows.append({
                "name": name,
                "label": f"{cfg.get('from', '?')} → {to_label}",
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
        self.use_days = False
        self.use_months = False
        self.use_years = False
        self.from_cols = []
        self.to_cols = []
        self.to_is_fixed = False
        self.to_fixed_value = ""

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

        # Reconstruct the to_fixed flag: a `to` that isn't a column is a fixed date.
        entries: Dict[str, str] = {}
        for name, cfg in existing.items():
            cfg = dict(cfg)
            cfg["to_fixed"] = cfg.get("to") not in cols
            entries[name] = json.dumps(cfg)

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

    # ------------------------------------------------------------------ #
    # Current selection                                                    #
    # ------------------------------------------------------------------ #

    @rx.event
    def set_use_days(self, value: bool):
        self.use_days = value

    @rx.event
    def set_use_months(self, value: bool):
        self.use_months = value

    @rx.event
    def set_use_years(self, value: bool):
        self.use_years = value

    @rx.event
    def toggle_from(self, col: str):
        if col in self.from_cols:
            self.from_cols = [c for c in self.from_cols if c != col]
        else:
            self.from_cols = self.from_cols + [col]

    @rx.event
    def toggle_to(self, col: str):
        if col in self.to_cols:
            self.to_cols = [c for c in self.to_cols if c != col]
        else:
            self.to_cols = self.to_cols + [col]

    @rx.event
    def set_to_is_fixed(self, value: bool):
        self.to_is_fixed = value

    @rx.event
    def set_to_fixed_value(self, value: str):
        self.to_fixed_value = value

    @rx.event
    def add_current(self):
        types = [
            t for t, on in (("days", self.use_days), ("months", self.use_months), ("years", self.use_years))
            if on
        ]
        if not types:
            yield rx.toast.error("Tick at least one difference type.")
            return
        if not self.from_cols:
            yield rx.toast.error("Pick at least one From column.")
            return

        if self.to_is_fixed:
            fixed = self.to_fixed_value.strip()
            if not fixed:
                yield rx.toast.error("Enter a fixed date for To (e.g. 2025-01).")
                return
            to_targets = [(fixed, True)]
        else:
            if not self.to_cols:
                yield rx.toast.error("Pick at least one To column or switch To to a fixed date.")
                return
            to_targets = [(c, False) for c in self.to_cols]

        new_entries = dict(self.entries)
        added = False
        for from_col in self.from_cols:
            for to_value, to_fixed in to_targets:
                if not to_fixed and from_col == to_value:
                    continue  # skip self-difference
                name = f"{from_col}__to__{to_value}"
                if name in new_entries:
                    try:
                        cfg = json.loads(new_entries[name])
                    except (ValueError, TypeError):
                        cfg = {"from": from_col, "to": to_value, "features": [], "to_fixed": to_fixed}
                else:
                    cfg = {"from": from_col, "to": to_value, "features": [], "to_fixed": to_fixed}
                feats = cfg.get("features", [])
                for t in types:
                    if t not in feats:
                        feats.append(t)
                cfg["features"] = feats
                new_entries[name] = json.dumps(cfg)
                added = True

        if not added:
            yield rx.toast.error("Nothing added — From and To overlap.")
            return
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
            to_fixed = bool(cfg.pop("to_fixed", False))  # internal flag — not for the backend
            differences[name] = cfg
            from_col = cfg.get("from")
            if from_col and from_col not in used_cols:
                used_cols.append(from_col)
            # A fixed-date `to` is not a column, so it must not enter features_to_transform.
            to_col = cfg.get("to")
            if not to_fixed and to_col and to_col not in used_cols:
                used_cols.append(to_col)

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
