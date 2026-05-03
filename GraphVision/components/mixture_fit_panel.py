"""
MixtureFitPanel — display component for 3-component distribution fit results.

Pure display: reads PlotState.mixture_result and PlotState.mixture_curves.
No state logic here.
"""
import reflex as rx

from ..models.plot_state import PlotState

_FAMILY_COLORS = {
    "Poisson": "blue",
    "Gamma": "orange",
    "Tweedie": "purple",
    "unknown": "gray",
}

_FAMILY_TIPS = {
    "Poisson": "Use for count data (frequency). Link: log.",
    "Gamma": "Use for positive continuous data (severity). Link: log or inverse.",
    "Tweedie": "Use for compound Poisson-Gamma (mixed zero/positive). Link: log.",
    "unknown": "Fitting did not converge. Try a different column.",
}


def _pct(val) -> rx.Component:
    return rx.text(
        rx.cond(val, (val * 100).to_string(), "—"),
        font_size="xs",
    )


def _row(label: str, val_expr, color: str = "black") -> rx.Component:
    return rx.hstack(
        rx.text(label, font_size="xs", color="gray", width="130px"),
        rx.text(val_expr, font_size="xs", color=color, font_weight="500"),
        spacing="2",
    )


def mixture_fit_panel() -> rx.Component:
    family = PlotState.mixture_result["recommended_family"]
    return rx.vstack(
        # ── Family badge ──────────────────────────────────────────────────
        rx.hstack(
            rx.text("Recommended GLM family:", font_size="sm", color="#374151"),
            rx.cond(
                family == "unknown",
                rx.callout.root(
                    rx.callout.text(
                        "Could not fit distribution. Column may be constant, "
                        "have too few unique values, or contain negative data.",
                        font_size="xs",
                    ),
                    color="gray",
                    size="1",
                ),
                rx.hstack(
                    rx.badge(family, color_scheme="blue", size="2"),
                    rx.tooltip(
                        rx.icon("info", size=14, color="#9ca3af"),
                        content=rx.cond(
                            family == "Poisson",
                            _FAMILY_TIPS["Poisson"],
                            rx.cond(
                                family == "Gamma",
                                _FAMILY_TIPS["Gamma"],
                                _FAMILY_TIPS["Tweedie"],
                            ),
                        ),
                    ),
                    spacing="1",
                    align_items="center",
                ),
            ),
            spacing="2",
            align_items="center",
            flex_wrap="wrap",
        ),
        # ── Component weights ─────────────────────────────────────────────
        rx.cond(
            family != "unknown",
            rx.vstack(
                rx.text(
                    "Component weights",
                    font_size="xs",
                    font_weight="600",
                    color="#374151",
                    padding_top="6px",
                ),
                _row(
                    "Exponential",
                    rx.cond(
                        PlotState.mixture_result["w_exp"],
                        (PlotState.mixture_result["w_exp"] * 100).to_string() + "%",
                        "0%",
                    ),
                ),
                _row(
                    "Gamma",
                    rx.cond(
                        PlotState.mixture_result["w_gamma"],
                        (PlotState.mixture_result["w_gamma"] * 100).to_string() + "%",
                        "0%",
                    ),
                ),
                _row(
                    "Poisson",
                    rx.cond(
                        PlotState.mixture_result["w_poisson"],
                        (PlotState.mixture_result["w_poisson"] * 100).to_string() + "%",
                        "0%",
                    ),
                ),
                spacing="1",
                width="100%",
            ),
        ),
        # ── Component curves chart ────────────────────────────────────────
        rx.cond(
            PlotState.mixture_curves,
            rx.vstack(
                rx.text(
                    "Component densities",
                    font_size="xs",
                    font_weight="600",
                    color="#374151",
                    padding_top="8px",
                ),
                rx.recharts.line_chart(
                    rx.recharts.line(
                        data_key="exp",
                        stroke="#f97316",
                        dot=False,
                        name="Exponential",
                        stroke_width=1,
                    ),
                    rx.recharts.line(
                        data_key="gamma",
                        stroke="#3b82f6",
                        dot=False,
                        name="Gamma",
                        stroke_width=1,
                    ),
                    rx.recharts.line(
                        data_key="poisson",
                        stroke="#8b5cf6",
                        dot=False,
                        name="Poisson",
                        stroke_width=1,
                    ),
                    rx.recharts.line(
                        data_key="total",
                        stroke="#ef4444",
                        dot=False,
                        name="Mixture total",
                        stroke_width=2,
                        stroke_dasharray="5 3",
                    ),
                    rx.recharts.x_axis(data_key="x", tick=False),
                    rx.recharts.y_axis(width=40),
                    rx.recharts.graphing_tooltip(),
                    rx.recharts.legend(),
                    data=PlotState.mixture_curves,
                    width="100%",
                    height=180,
                ),
                width="100%",
                spacing="1",
            ),
        ),
        width="100%",
        spacing="2",
        padding="8px",
        border="1px solid #e5e7eb",
        border_radius="6px",
        background="#fafafa",
    )
