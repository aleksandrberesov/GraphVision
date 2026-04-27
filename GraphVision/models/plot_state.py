from __future__ import annotations

from typing import Any, Dict, List, Optional

import reflex as rx


def _corr_color(val: float) -> str:
    """Map correlation value [-1, 1] to a hex color (blue → white → red)."""
    v = max(-1.0, min(1.0, val))
    if v >= 0:
        r = int(255 - 16 * v)
        g = int(255 - 187 * v)
        b = int(255 - 187 * v)
    else:
        a = -v
        r = int(255 - 196 * a)
        g = int(255 - 125 * a)
        b = int(255 - 9 * a)
    return f"#{r:02x}{g:02x}{b:02x}"


class PlotState(rx.State):
    is_open: bool = False
    current_node_id: str = ""
    column_names: List[str] = []
    selected_column: str = ""
    # [{x: str, count: float}, ...] for bar chart
    dist_data: List[Dict[str, Any]] = []
    dist_stats_str: str = ""
    corr_html: str = ""

    @rx.event
    def open_modal(self):
        self.is_open = True

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    @rx.event
    def load_for_node(self, node_id: str):
        self.current_node_id = node_id
        self.dist_data = []
        self.dist_stats_str = ""
        self.corr_html = ""

        if not node_id:
            self.column_names = []
            self.selected_column = ""
            return

        from . import pipeline_hooks
        session_id = self.router.session.client_token

        cols_by_type: Optional[Dict[str, List[str]]] = pipeline_hooks.get_vertex_columns(
            session_id, node_id
        )
        if not cols_by_type:
            self.column_names = []
            self.selected_column = ""
            return

        cols: List[str] = []
        for col_list in cols_by_type.values():
            cols.extend(col_list)
        self.column_names = cols

        if cols:
            self.selected_column = cols[0]
            self._load_distribution(session_id, node_id, cols[0])

        self._load_correlation(session_id, node_id)

    @rx.event
    def change_column(self, column: str):
        self.selected_column = column
        self._load_distribution(
            self.router.session.client_token, self.current_node_id, column
        )

    # ------------------------------------------------------------------
    # Internal helpers (not event handlers)
    # ------------------------------------------------------------------

    def _load_distribution(self, session_id: str, node_id: str, column: str) -> None:
        from . import pipeline_hooks

        result = pipeline_hooks.compute_distribution(session_id, node_id, column)
        if not result:
            self.dist_data = []
            self.dist_stats_str = ""
            return

        histogram: List[float] = result.get("histogram", [])
        self.dist_data = [
            {"x": str(i), "count": float(v)} for i, v in enumerate(histogram)
        ]

        stats = result.get("statistics", {})
        if "mean" in stats:
            self.dist_stats_str = (
                f"Mean: {stats['mean']:.2f}  "
                f"Std: {stats['std']:.2f}  "
                f"Min: {stats['min']:.2f}  "
                f"Max: {stats['max']:.2f}  "
                f"N: {stats['count']}"
            )
        elif "unique" in stats:
            self.dist_stats_str = (
                f"Unique: {stats['unique']}  "
                f"Top: {stats.get('top', '—')}  "
                f"N: {stats['count']}"
            )
        else:
            self.dist_stats_str = ""

    def _load_correlation(self, session_id: str, node_id: str) -> None:
        from . import pipeline_hooks

        matrix = pipeline_hooks.compute_correlation(session_id, node_id, "pearson")
        if not matrix:
            self.corr_html = ""
            return

        cols = list(matrix.keys())
        cell_style = "width:48px;height:36px;text-align:center;font-size:9px;border:1px solid #e2e8f0"
        hdr_style = "width:48px;font-size:9px;text-align:center;padding:2px"
        lbl_style = "width:80px;font-size:9px;text-align:right;padding-right:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis"

        header = "<tr><th style='width:80px'></th>" + "".join(
            f"<th style='{hdr_style}' title='{c}'>{c[:6]}</th>" for c in cols
        ) + "</tr>"

        data_rows = ""
        for row_col in cols:
            raw = matrix.get(row_col, {})
            cells = ""
            for col in cols:
                val = float(raw.get(col, 0.0)) if isinstance(raw, dict) else 0.0
                color = _corr_color(val)
                cells += f"<td style='{cell_style};background:{color}' title='{row_col} / {col}'>{val:.2f}</td>"
            data_rows += f"<tr><td style='{lbl_style}' title='{row_col}'>{row_col}</td>{cells}</tr>"

        self.corr_html = (
            "<div style='overflow:auto;max-height:300px;width:100%'>"
            f"<table style='border-collapse:collapse'>{header}{data_rows}</table>"
            "</div>"
        )
