from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx


class FilterState(rx.State):
    is_open: bool = False
    current_node_id: str = ""
    # [{col, type, top_values or min/max}] from get_column_filter_options
    filter_columns: List[Dict[str, Any]] = []
    total_row_count: int = 0

    # Categorical selections — flat "col__value" strings to avoid nested state
    checked_cat_keys: List[str] = []

    # Numeric range inputs per column — stored as strings so the input field is editable
    num_lo: Dict[str, str] = {}
    num_hi: Dict[str, str] = {}

    @rx.var
    def active_filter_spec(self) -> List[Dict[str, Any]]:
        """Build a filter_spec list from current UI state (fed into analytics hooks)."""
        spec: List[Dict[str, Any]] = []

        for col_meta in self.filter_columns:
            col = col_meta["col"]
            col_type = col_meta["type"]

            if col_type == "categorical":
                prefix = col + "__"
                selected = [
                    k[len(prefix):]
                    for k in self.checked_cat_keys
                    if k.startswith(prefix)
                ]
                if selected:
                    spec.append({"type": "categorical", "column": col, "values": selected})

            elif col_type == "numeric":
                lo_str = self.num_lo.get(col, "")
                hi_str = self.num_hi.get(col, "")
                lo = float(lo_str) if lo_str.strip() else None
                hi = float(hi_str) if hi_str.strip() else None
                if lo is not None or hi is not None:
                    spec.append({"type": "numeric", "column": col, "range": [lo, hi]})

        return spec

    @rx.var
    def is_filter_active(self) -> bool:
        return len(self.active_filter_spec) > 0

    @rx.var
    def active_filter_count(self) -> int:
        return len(self.active_filter_spec)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    @rx.event
    def toggle_open(self):
        self.is_open = not self.is_open

    @rx.event
    def toggle_cat_key(self, key: str, checked: bool):
        if checked:
            if key not in self.checked_cat_keys:
                self.checked_cat_keys = self.checked_cat_keys + [key]
        else:
            self.checked_cat_keys = [k for k in self.checked_cat_keys if k != key]

    @rx.event
    def set_num_lo(self, col: str, val: str):
        self.num_lo = {**self.num_lo, col: val}

    @rx.event
    def set_num_hi(self, col: str, val: str):
        self.num_hi = {**self.num_hi, col: val}

    @rx.event
    def clear_filters(self):
        self.checked_cat_keys = []
        self.num_lo = {}
        self.num_hi = {}

    @rx.event
    async def load_options(self, session_id: str, node_id: str):
        from . import pipeline_hooks
        self.current_node_id = node_id
        self.checked_cat_keys = []
        self.num_lo = {}
        self.num_hi = {}
        result = pipeline_hooks.get_column_filter_options(session_id, node_id)
        if result:
            self.filter_columns = result.get("columns", [])
            self.total_row_count = result.get("total_row_count", 0)
        else:
            self.filter_columns = []
            self.total_row_count = 0
