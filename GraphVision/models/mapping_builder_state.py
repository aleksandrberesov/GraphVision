"""
State for the Category Mapping Builder dialog (Phase 4 — multi-select → merge).

The user picks categorical columns, then for the active column: sorts/searches its
values (chips show frequency %, e.g. "Lada (18.8%)"), multi-selects several values,
names a group, and clicks **Merge** — all selected values are mapped to that group.

The output is unchanged: GLMCategoryMappingTransformation's

    {features_to_transform, mappings: {col: {original_value: group}},
     unknown_strategy, keep_original}

Each column's map is **identity by default** (value → itself) with merge overrides on
top, so values the user never merges pass through unchanged rather than being routed
to ``unknown_strategy``.
"""

from __future__ import annotations

import json
from collections import defaultdict
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
    # Active column being edited
    active_column: str = ""

    # Per-column caches (JSON strings keep the reactive state simple):
    #   freqs_cache[col]    -> JSON list of {value, count, pct}
    #   saved_mappings[col] -> JSON dict {value: group} (identity default + merges)
    freqs_cache: Dict[str, str] = {}
    saved_mappings: Dict[str, str] = {}

    # Active-column controls
    sort_mode: str = "frequency"   # "frequency" | "alphabet"  (embedding = 4b, deferred)
    search: str = ""
    hide_merged: bool = False
    selected_values: List[str] = []
    group_name: str = ""

    unknown_strategy: str = "unknown"
    keep_original: bool = True

    # ------------------------------------------------------------------ #
    # Computed                                                             #
    # ------------------------------------------------------------------ #

    @rx.var
    def can_submit(self) -> bool:
        return bool(self.selected_features)

    @rx.var
    def can_merge(self) -> bool:
        return bool(self.selected_values) and bool(self.group_name.strip())

    @rx.var
    def active_values_view(self) -> List[Dict[str, Any]]:
        """Chips for the active column: frequency-formatted, filtered, sorted."""
        if not self.active_column:
            return []
        freqs = json.loads(self.freqs_cache.get(self.active_column, "[]"))
        group_map = json.loads(self.saved_mappings.get(self.active_column, "{}"))
        q = self.search.strip().lower()
        items: List[Dict[str, Any]] = []
        for f in freqs:
            val = f["value"]
            if q and q not in val.lower():
                continue
            group = group_map.get(val, val)
            is_merged = group != val
            if self.hide_merged and is_merged:
                continue
            items.append({
                "value": val,
                "label": f"{val} ({f['pct']}%)",
                "group": group,
                "is_merged": is_merged,
                "is_selected": val in self.selected_values,
            })
        if self.sort_mode == "alphabet":
            items.sort(key=lambda d: d["value"].lower())
        # "frequency": freqs already arrive most-frequent first
        return items

    @rx.var
    def merged_groups(self) -> List[Dict[str, str]]:
        """Summary of the merges defined for the active column."""
        if not self.active_column:
            return []
        group_map = json.loads(self.saved_mappings.get(self.active_column, "{}"))
        groups: Dict[str, List[str]] = defaultdict(list)
        for val, grp in group_map.items():
            if grp != val:
                groups[grp].append(val)
        return [
            {"group": g, "members": ", ".join(sorted(members)),
             "count": str(len(members))}
            for g, members in sorted(groups.items())
        ]

    # ------------------------------------------------------------------ #
    # Open / close                                                         #
    # ------------------------------------------------------------------ #

    async def _load_cat_columns(self, parent_vertex_id: str) -> List[str]:
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"
        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_vertex_id)
        if cols_by_type:
            return (
                cols_by_type.get("categorical", [])
                + cols_by_type.get("ordered_categorical", [])
            )
        return []

    def _reset_active_controls(self):
        self.selected_values = []
        self.group_name = ""
        self.search = ""

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        """Open in add-mode for the given parent vertex."""
        from .busy_state import BusyState

        yield BusyState.show("Loading columns…")
        cat_cols = await self._load_cat_columns(parent_vertex_id)
        yield BusyState.hide()

        self.parent_vertex_id = parent_vertex_id
        self.available_columns = cat_cols
        self.selected_features = []
        self.active_column = ""
        self.freqs_cache = {}
        self.saved_mappings = {}
        self._reset_active_controls()
        self.sort_mode = "frequency"
        self.hide_merged = False
        self.unknown_strategy = "unknown"
        self.keep_original = True
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
        cat_cols = await self._load_cat_columns(parent_id)
        yield BusyState.hide()

        existing_mappings: Dict[str, Dict[str, str]] = existing_config.get("mappings", {})
        saved: Dict[str, str] = {
            col: json.dumps(val_map) for col, val_map in existing_mappings.items()
        }

        self.parent_vertex_id = parent_id
        self.available_columns = cat_cols
        self.selected_features = list(existing_mappings.keys())
        self.active_column = ""
        self.freqs_cache = {}
        self.saved_mappings = saved
        self._reset_active_controls()
        self.sort_mode = "frequency"
        self.hide_merged = False
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

    @rx.event
    async def toggle_feature(self, col: str):
        """Add or remove a column from the mapping selection."""
        if col in self.selected_features:
            self.selected_features = [c for c in self.selected_features if c != col]
            if self.active_column == col:
                self.active_column = ""
                self._reset_active_controls()
        else:
            self.selected_features = self.selected_features + [col]
            yield MappingBuilderState.set_active_column(col)

    @rx.event
    async def set_active_column(self, col: str):
        """Switch the column being edited; loads value frequencies on first visit."""
        if col == self.active_column:
            return
        self.active_column = col
        self._reset_active_controls()

        # Load value frequencies (cache per column).
        if col not in self.freqs_cache:
            from . import pipeline_hooks
            from .auth_state import AuthState
            from .graph import GraphState

            graph_state = await self.get_state(GraphState)
            session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
            freqs = pipeline_hooks.get_value_frequencies(
                session_id, self.parent_vertex_id, col
            ) or []
            self.freqs_cache = {**self.freqs_cache, col: json.dumps(freqs)}

        # Ensure the column's map covers every value: identity by default, with any
        # existing overrides (edit mode / prior merges) preserved.
        freqs = json.loads(self.freqs_cache.get(col, "[]"))
        existing = json.loads(self.saved_mappings.get(col, "{}"))
        gm: Dict[str, str] = {f["value"]: existing.get(f["value"], f["value"]) for f in freqs}
        for k, v in existing.items():   # keep overrides for values beyond the cap
            gm.setdefault(k, v)
        self.saved_mappings = {**self.saved_mappings, col: json.dumps(gm)}

    # ------------------------------------------------------------------ #
    # Active-column controls                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    def set_sort_mode(self, mode: str):
        self.sort_mode = mode

    @rx.event
    def set_search(self, value: str):
        self.search = value

    @rx.event
    def set_hide_merged(self, value: bool):
        self.hide_merged = value

    @rx.event
    def set_group_name(self, value: str):
        self.group_name = value

    @rx.event
    def toggle_value(self, value: str):
        if value in self.selected_values:
            self.selected_values = [v for v in self.selected_values if v != value]
        else:
            self.selected_values = self.selected_values + [value]

    @rx.event
    def merge(self):
        """Map every selected value to the group name."""
        if not self.selected_values:
            yield rx.toast.error("Select one or more values to merge.")
            return
        name = self.group_name.strip()
        if not name:
            yield rx.toast.error("Enter a group name.")
            return
        gm = json.loads(self.saved_mappings.get(self.active_column, "{}"))
        for v in self.selected_values:
            gm[v] = name
        self.saved_mappings = {**self.saved_mappings, self.active_column: json.dumps(gm)}
        self.selected_values = []
        self.group_name = ""

    @rx.event
    def reset_selection(self):
        """Reset: clear the current selection + group-name input (keeps merges)."""
        self.selected_values = []
        self.group_name = ""

    @rx.event
    def clear_merges(self):
        """Clear: undo all merges for the active column (back to identity)."""
        freqs = json.loads(self.freqs_cache.get(self.active_column, "[]"))
        gm = {f["value"]: f["value"] for f in freqs}
        self.saved_mappings = {**self.saved_mappings, self.active_column: json.dumps(gm)}
        self.selected_values = []
        self.group_name = ""

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
