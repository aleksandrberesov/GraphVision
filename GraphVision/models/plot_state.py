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


_STABILITY_META: List[tuple] = [
    ("condition_number", "Condition number",
     "Ratio of largest to smallest eigenvalue. >1000 may indicate ill-conditioning."),
    ("rank", "Rank",
     "Effective rank of the matrix. Should equal the number of columns."),
    ("determinant", "Determinant",
     "Matrix determinant. Near zero indicates near-linear dependence."),
    ("eigenvalue_min", "Eigenvalue (min)",
     "Smallest eigenvalue. Near zero suggests rank deficiency."),
    ("eigenvalue_max", "Eigenvalue (max)",
     "Largest eigenvalue."),
    ("vif_max", "VIF max",
     "Maximum Variance Inflation Factor. >10 indicates strong multicollinearity."),
]


def _build_stability_html(stability: Dict[str, Any]) -> str:
    if not stability:
        return ""
    expected_rank = stability.get("expected_rank")
    td = "padding:3px 8px;font-size:10px"
    rows_html = ""
    for key, label, tooltip in _STABILITY_META:
        val = stability.get(key)
        if val is None:
            continue
        if key == "rank":
            val_str = str(int(val))
            if expected_rank is not None and int(val) < int(expected_rank):
                val_str = f"{val_str} / {expected_rank}"
                color = "#ef4444"
            else:
                color = "inherit"
        else:
            val_str = f"{float(val):.4g}"
            if key == "condition_number" and float(val) > 1000:
                color = "#ef4444"
            elif key == "vif_max" and float(val) > 10:
                color = "#f97316"
            else:
                color = "inherit"
        rows_html += (
            f"<tr>"
            f"<td style='{td}' title='{tooltip}'>{label}</td>"
            f"<td style='{td};text-align:right;color:{color};font-weight:500'>{val_str}</td>"
            f"</tr>"
        )
    if not rows_html:
        return ""
    return (
        "<div style='margin-top:12px'>"
        "<div style='font-size:11px;font-weight:600;color:#374151;margin-bottom:4px'>"
        "Matrix stability (Pearson)</div>"
        "<table style='border-collapse:collapse;width:100%;background:#f9fafb;"
        "border-radius:4px;border:1px solid #e5e7eb'>"
        f"<thead><tr>"
        f"<th style='{td};color:#6b7280;border-bottom:1px solid #e5e7eb;text-align:left'>Metric</th>"
        f"<th style='{td};color:#6b7280;border-bottom:1px solid #e5e7eb;text-align:right'>Value</th>"
        f"</tr></thead>"
        f"<tbody>{rows_html}</tbody>"
        "</table></div>"
    )


class PlotState(rx.State):
    is_open: bool = False
    current_node_id: str = ""
    column_names: List[str] = []
    selected_column: str = ""
    # [{x: str, count: float}, ...] for bar chart
    dist_data: List[Dict[str, Any]] = []
    dist_stats_str: str = ""
    is_numeric_dist: bool = False
    mixture_result: Dict[str, Any] = {}
    mixture_curves: List[Dict[str, Any]] = []
    is_fitting: bool = False
    corr_html: str = ""
    corr_stability_html: str = ""

    @rx.event
    def open_modal(self):
        self.is_open = True

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    @rx.event
    async def load_for_node(self, node_id: str):
        from .auth_state import AuthState
        self.current_node_id = node_id
        self.dist_data = []
        self.dist_stats_str = ""
        self.is_numeric_dist = False
        self.mixture_result = {}
        self.mixture_curves = []
        self.is_fitting = False
        self.corr_html = ""
        self.corr_stability_html = ""

        if not node_id:
            self.column_names = []
            self.selected_column = ""
            return

        from . import pipeline_hooks
        session_id = (await self.get_state(AuthState)).user_id

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
    async def change_column(self, column: str):
        from .auth_state import AuthState
        self.selected_column = column
        self.mixture_result = {}
        self.mixture_curves = []
        session_id = (await self.get_state(AuthState)).user_id
        self._load_distribution(session_id, self.current_node_id, column)

    @rx.event
    async def fit_distribution(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        self.is_fitting = True
        yield
        session_id = (await self.get_state(AuthState)).user_id
        result = pipeline_hooks.fit_column_distribution(
            session_id, self.current_node_id, self.selected_column
        )
        if result:
            self.mixture_result = result.get("mixture", {})
            self.mixture_curves = result.get("curves", [])
        else:
            self.mixture_result = {}
            self.mixture_curves = []
        self.is_fitting = False

    # ------------------------------------------------------------------
    # Internal helpers (not event handlers)
    # ------------------------------------------------------------------

    def _load_distribution(self, session_id: str, node_id: str, column: str) -> None:
        from . import pipeline_hooks

        result = pipeline_hooks.compute_distribution(session_id, node_id, column)
        if not result:
            self.dist_data = []
            self.dist_stats_str = ""
            self.is_numeric_dist = False
            return

        histogram: List[float] = result.get("histogram", [])
        kde_curve: List[Dict[str, Any]] = result.get("kde_curve", [])

        if kde_curve and histogram:
            # Merge: for each histogram bin, sample the nearest KDE density value.
            # This produces a unified 50-point dataset usable in ComposedChart.
            n_bins = len(histogram)
            n_kde = len(kde_curve)
            merged = []
            for i, count in enumerate(histogram):
                kde_idx = min(int(i * n_kde / n_bins), n_kde - 1)
                merged.append({
                    "x": str(i),
                    "count": float(count),
                    "kde": float(kde_curve[kde_idx]["y"]),
                })
            self.dist_data = merged
            self.is_numeric_dist = True
        else:
            self.dist_data = [
                {"x": str(i), "count": float(v)} for i, v in enumerate(histogram)
            ]
            self.is_numeric_dist = False

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

        result = pipeline_hooks.compute_correlation(session_id, node_id, "pearson")
        if not result:
            self.corr_html = ""
            self.corr_stability_html = ""
            return

        # Support both legacy {col: {row: float}} and new {"matrix": ..., "stability": ...}
        if "matrix" in result and isinstance(result.get("matrix"), dict):
            matrix = result["matrix"]
            stability = result.get("stability") or {}
        else:
            matrix = result
            stability = {}

        self.corr_stability_html = _build_stability_html(stability)

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
