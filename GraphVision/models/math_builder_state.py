"""
State for the Mathematical Transform Builder dialog.

Lets the user pick numeric columns and stack one or more math transforms
on each (log / double_log / exp / power-range / power-list), then assembles
the nested ``transformations`` dict required by
``GLMMathematicalTransformation``:

    {col: {'log': [1], 'double_log': True, 'exp': True,
           'power': {'from': -1, 'to': 3}}}        # or  'power': [0.5, 2, 3]

Flow: tick transform type(s) → (fill power fields) → pick columns → "+ Add"
(accumulates into ``entries``) → repeat → "Add"/"Save" creates the node.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import reflex as rx


class MathBuilderState(rx.State):
    """Dialog state for the visual mathematical-transform builder."""

    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    # Numeric columns available at the parent vertex
    available_columns: List[str] = []
    # Columns selected for the *current* "+ Add" action
    selected_features: List[str] = []

    # Current transform-type selection (the checkboxes)
    use_log: bool = False
    use_double_log: bool = False
    use_exp: bool = False
    use_power_range: bool = False
    use_power_list: bool = False

    # Conditional fields
    pr_from: str = ""
    pr_to: str = ""
    pl_values: str = ""

    # Accumulated config: {col: JSON string of its transform dict}
    entries: Dict[str, str] = {}

    # ------------------------------------------------------------------ #
    # Computed                                                             #
    # ------------------------------------------------------------------ #

    @rx.var
    def can_submit(self) -> bool:
        return bool(self.entries)

    @rx.var
    def entry_rows(self) -> List[Dict[str, str]]:
        """Human-readable summary rows for the accumulated entries."""
        rows: List[Dict[str, str]] = []
        for col, cfg_json in self.entries.items():
            try:
                cfg = json.loads(cfg_json)
            except (ValueError, TypeError):
                cfg = {}
            parts: List[str] = []
            if "log" in cfg:
                parts.append("log")
            if cfg.get("double_log"):
                parts.append("double_log")
            if cfg.get("exp"):
                parts.append("exp")
            if "power" in cfg:
                p = cfg["power"]
                if isinstance(p, dict):
                    parts.append(f"power[{p.get('from')}..{p.get('to')}]")
                else:
                    parts.append(f"power{p}")
            rows.append({"col": col, "summary": ", ".join(parts)})
        return rows

    # ------------------------------------------------------------------ #
    # Open / close                                                         #
    # ------------------------------------------------------------------ #

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

    def _reset_all(self):
        self.selected_features = []
        self.entries = {}
        self._reset_current()

    def _reset_current(self):
        self.use_log = False
        self.use_double_log = False
        self.use_exp = False
        self.use_power_range = False
        self.use_power_list = False
        self.pr_from = ""
        self.pr_to = ""
        self.pl_values = ""

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        """Open in add-mode for the given parent vertex."""
        from .busy_state import BusyState

        yield BusyState.show("Loading columns…")
        cols = await self._load_numeric_columns(parent_vertex_id)
        yield BusyState.hide()

        self.parent_vertex_id = parent_vertex_id
        self.available_columns = cols
        self._reset_all()
        self.is_edit_mode = False
        self.vertex_id_editing = ""
        self.is_open = True

    @rx.event
    async def open_edit_dialog(self, vertex_id: str, existing_config: Dict[str, Any]):
        """Open in edit-mode pre-filled with existing config."""
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

        existing: Dict[str, Dict[str, Any]] = existing_config.get("transformations", {})

        self.parent_vertex_id = parent_id
        self.available_columns = cols
        self._reset_current()
        self.selected_features = []
        self.entries = {col: json.dumps(cfg) for col, cfg in existing.items()}
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
    # Current selection editing                                            #
    # ------------------------------------------------------------------ #

    @rx.event
    def set_use_log(self, value: bool):
        self.use_log = value

    @rx.event
    def set_use_double_log(self, value: bool):
        self.use_double_log = value

    @rx.event
    def set_use_exp(self, value: bool):
        self.use_exp = value

    @rx.event
    def set_use_power_range(self, value: bool):
        # power-range and power-list both write the 'power' key — mutually exclusive
        self.use_power_range = value
        if value:
            self.use_power_list = False

    @rx.event
    def set_use_power_list(self, value: bool):
        self.use_power_list = value
        if value:
            self.use_power_range = False

    @rx.event
    def set_pr_from(self, value: str):
        self.pr_from = value

    @rx.event
    def set_pr_to(self, value: str):
        self.pr_to = value

    @rx.event
    def set_pl_values(self, value: str):
        self.pl_values = value

    @rx.event
    def toggle_feature(self, col: str):
        if col in self.selected_features:
            self.selected_features = [c for c in self.selected_features if c != col]
        else:
            self.selected_features = self.selected_features + [col]

    # ------------------------------------------------------------------ #
    # Accumulate / clear                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_float(s: str) -> Optional[float]:
        try:
            return float(s.strip().replace(",", "."))
        except (ValueError, AttributeError):
            return None

    def _build_partial(self) -> Tuple[Optional[Dict[str, Any]], str]:
        """Build the transform dict for the current selection, or (None, error)."""
        partial: Dict[str, Any] = {}
        if self.use_log:
            partial["log"] = [1]
        if self.use_double_log:
            partial["double_log"] = True
        if self.use_exp:
            partial["exp"] = True
        if self.use_power_range:
            a = self._parse_float(self.pr_from)
            b = self._parse_float(self.pr_to)
            if a is None or b is None:
                return None, "Power range needs numeric From and To."
            partial["power"] = {"from": a, "to": b}
        elif self.use_power_list:
            vals: List[float] = []
            for tok in self.pl_values.split(","):
                tok = tok.strip()
                if not tok:
                    continue
                f = self._parse_float(tok)
                if f is None:
                    return None, f"Invalid power value: '{tok}'"
                vals.append(f)
            if not vals:
                return None, "Enter at least one power value (e.g. -1, 0.5, 2, 3)."
            partial["power"] = vals
        return partial, ""

    @rx.event
    def add_current(self):
        if not self.selected_features:
            yield rx.toast.error("Select at least one column.")
            return
        partial, err = self._build_partial()
        if err:
            yield rx.toast.error(err)
            return
        if not partial:
            yield rx.toast.error("Tick at least one transformation type.")
            return

        new_entries = dict(self.entries)
        for col in self.selected_features:
            try:
                existing = json.loads(new_entries[col]) if col in new_entries else {}
            except (ValueError, TypeError):
                existing = {}
            existing.update(partial)
            new_entries[col] = json.dumps(existing)
        self.entries = new_entries
        self.selected_features = []
        self._reset_current()

    @rx.event
    def remove_entry(self, col: str):
        self.entries = {k: v for k, v in self.entries.items() if k != col}

    @rx.event
    def clear_entries(self):
        self.entries = {}

    # ------------------------------------------------------------------ #
    # Submit                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def submit(self):
        if not self.entries:
            yield rx.toast.error("Add at least one column transformation.")
            return

        transformations: Dict[str, Dict[str, Any]] = {}
        for col, cfg_json in self.entries.items():
            try:
                transformations[col] = json.loads(cfg_json)
            except (ValueError, TypeError):
                transformations[col] = {}

        config: Dict[str, Any] = {
            "features_to_transform": list(transformations.keys()),
            "transformations": transformations,
            "keep_original": True,
        }

        from .graph import GraphState
        graph_state = await self.get_state(GraphState)
        self.is_open = False

        if self.is_edit_mode:
            vertex_id = self.vertex_id_editing
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.apply_config_edit(vertex_id, "GLMMathematicalTransformation", config)
        else:
            if self.parent_vertex_id:
                yield graph_state._select_node(self.parent_vertex_id)
            yield GraphState.add_transformation_node("GLMMathematicalTransformation", config)
