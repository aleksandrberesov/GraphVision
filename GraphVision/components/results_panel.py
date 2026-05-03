import reflex as rx

from ..models.plot_state import PlotState  # noqa: F401 — PlotState must be imported to register its state
from ..models import NodeState
from .mixture_fit_panel import mixture_fit_panel


def _dist_chart() -> rx.Component:
    return rx.cond(
        PlotState.is_numeric_dist,
        rx.recharts.composed_chart(
            rx.recharts.bar(
                data_key="count",
                fill="#3B82F6",
                fill_opacity=0.5,
                y_axis_id="left",
                name="Count",
            ),
            rx.recharts.line(
                data_key="kde",
                stroke="#ef4444",
                dot=False,
                y_axis_id="right",
                name="Density (KDE)",
            ),
            rx.recharts.x_axis(data_key="x", tick=False),
            rx.recharts.y_axis(y_axis_id="left", orientation="left", width=40),
            rx.recharts.y_axis(y_axis_id="right", orientation="right", width=40),
            rx.recharts.graphing_tooltip(),
            rx.recharts.legend(),
            data=PlotState.dist_data,
            width="100%",
            height=220,
        ),
        rx.recharts.bar_chart(
            rx.recharts.bar(data_key="count", fill="#3B82F6"),
            rx.recharts.x_axis(data_key="x", tick=False),
            rx.recharts.y_axis(),
            rx.recharts.graphing_tooltip(),
            data=PlotState.dist_data,
            width="100%",
            height=220,
        ),
    )


def _distribution_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Column:", font_size="sm", color="black"),
            rx.select(
                PlotState.column_names,
                value=PlotState.selected_column,
                on_change=PlotState.change_column,
                width="200px",
            ),
            align_items="center",
            spacing="2",
        ),
        rx.cond(
            PlotState.dist_data,
            rx.vstack(
                _dist_chart(),
                rx.text(
                    PlotState.dist_stats_str,
                    font_size="xs",
                    color="gray",
                    text_align="center",
                ),
                # "Fit distribution" button — numeric columns only
                rx.cond(
                    PlotState.is_numeric_dist,
                    rx.hstack(
                        rx.button(
                            rx.cond(
                                PlotState.is_fitting,
                                rx.hstack(
                                    rx.spinner(size="1"),
                                    rx.text("Fitting…"),
                                    spacing="1",
                                    align_items="center",
                                ),
                                rx.text("Fit distribution"),
                            ),
                            on_click=PlotState.fit_distribution,
                            disabled=PlotState.is_fitting,
                            size="1",
                            variant="soft",
                            color_scheme="blue",
                        ),
                        justify="end",
                        width="100%",
                    ),
                ),
                # Mixture fit panel — shown once results are available
                rx.cond(
                    PlotState.mixture_result,
                    mixture_fit_panel(),
                ),
                width="100%",
                spacing="2",
            ),
            rx.text(
                "No data — select a manifested node.",
                color="gray",
                font_size="sm",
                font_style="italic",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _correlation_tab() -> rx.Component:
    return rx.cond(
        PlotState.corr_html != "",
        rx.vstack(
            rx.html(PlotState.corr_html),
            rx.cond(
                PlotState.corr_stability_html != "",
                rx.html(PlotState.corr_stability_html),
            ),
            width="100%",
            spacing="1",
        ),
        rx.text(
            "No correlation data — select a manifested node.",
            color="gray",
            font_size="sm",
            font_style="italic",
        ),
    )


def _feature_importance_tab() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.button(
                rx.cond(
                    PlotState.fi_is_computing,
                    rx.hstack(rx.spinner(size="1"), rx.text("Computing…"), spacing="1", align_items="center"),
                    rx.text("Compute"),
                ),
                on_click=PlotState.compute_feature_importance,
                disabled=PlotState.fi_is_computing,
                size="1",
                variant="soft",
                color_scheme="blue",
            ),
            rx.select(
                ["10", "20", "All"],
                value=PlotState.fi_top_n_str,
                on_change=PlotState.set_fi_top_n,
                width="80px",
                size="1",
            ),
            rx.text("features", font_size="xs", color="gray"),
            spacing="2",
            align_items="center",
        ),
        rx.cond(
            PlotState.fi_warning != "",
            rx.callout.root(
                rx.callout.text(PlotState.fi_warning, font_size="xs"),
                color="gray",
                size="1",
            ),
        ),
        rx.cond(
            PlotState.feature_importances_display,
            rx.vstack(
                rx.recharts.bar_chart(
                    rx.recharts.bar(
                        data_key="importance",
                        fill="#3b82f6",
                        name="Importance",
                    ),
                    rx.recharts.x_axis(type="number", tick_count=5),
                    rx.recharts.y_axis(
                        data_key="feature",
                        type="category",
                        width=120,
                    ),
                    rx.recharts.graphing_tooltip(),
                    data=PlotState.feature_importances_display,
                    layout="vertical",
                    width="100%",
                    height=rx.cond(
                        PlotState.fi_top_n_str == "All",
                        500,
                        rx.cond(PlotState.fi_top_n_str == "20", 380, 220),
                    ),
                ),
                rx.text(
                    "Model R² = " + PlotState.fi_model_r2.to_string(),
                    font_size="xs",
                    color="gray",
                ),
                width="100%",
                spacing="2",
            ),
        ),
        width="100%",
        spacing="3",
    )


def _multivariate_tab() -> rx.Component:
    return rx.vstack(
        # Column selectors
        rx.hstack(
            rx.vstack(
                rx.text("Value (numeric)", font_size="xs", color="gray"),
                rx.select(
                    PlotState.numeric_column_names,
                    value=PlotState.mv_value_col,
                    on_change=PlotState.set_mv_value_col,
                    placeholder="Select…",
                    width="160px",
                    size="1",
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Split by (primary)", font_size="xs", color="gray"),
                rx.select(
                    PlotState.categorical_column_names,
                    value=PlotState.mv_primary_col,
                    on_change=PlotState.set_mv_primary_col,
                    placeholder="Select…",
                    width="160px",
                    size="1",
                ),
                spacing="1",
            ),
            rx.vstack(
                rx.text("Group by (secondary)", font_size="xs", color="gray"),
                rx.select(
                    PlotState.categorical_column_names,
                    value=PlotState.mv_secondary_col,
                    on_change=PlotState.set_mv_secondary_col,
                    placeholder="Select…",
                    width="160px",
                    size="1",
                ),
                spacing="1",
            ),
            spacing="3",
            flex_wrap="wrap",
        ),
        rx.button(
            rx.cond(
                PlotState.mv_is_loading,
                rx.hstack(rx.spinner(size="1"), rx.text("Loading…"), spacing="1", align_items="center"),
                rx.text("Apply"),
            ),
            on_click=PlotState.apply_grouped_stats,
            disabled=PlotState.mv_is_loading,
            size="1",
            variant="soft",
            color_scheme="blue",
        ),
        rx.cond(
            PlotState.mv_warning != "",
            rx.callout.root(
                rx.callout.text(PlotState.mv_warning, font_size="xs"),
                color="gray",
                size="1",
            ),
        ),
        rx.cond(
            PlotState.mv_data,
            rx.recharts.bar_chart(
                rx.foreach(
                    PlotState.mv_bar_specs,
                    lambda spec: rx.recharts.bar(
                        data_key=spec["cat_name"],
                        fill=spec["color"],
                        name=spec["cat_name"],
                    ),
                ),
                rx.recharts.x_axis(data_key="primary_cat"),
                rx.recharts.y_axis(width=50),
                rx.recharts.graphing_tooltip(),
                rx.recharts.legend(),
                data=PlotState.mv_data,
                width="100%",
                height=280,
            ),
        ),
        width="100%",
        spacing="3",
    )


def results_panel() -> rx.Component:
    return rx.fragment(
        rx.button(
            "View plots",
            on_click=PlotState.load_for_node(NodeState.id),
            disabled=NodeState.status == "",
            width="100%",
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Data at selected node"),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Distribution", value="dist"),
                        rx.tabs.trigger("Correlation", value="corr"),
                        rx.tabs.trigger("Feature Importance", value="fi"),
                        rx.tabs.trigger("Multivariate", value="mv"),
                    ),
                    rx.tabs.content(_distribution_tab(), value="dist"),
                    rx.tabs.content(_correlation_tab(), value="corr"),
                    rx.tabs.content(_feature_importance_tab(), value="fi"),
                    rx.tabs.content(_multivariate_tab(), value="mv"),
                    default_value="dist",
                    width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Close", variant="outline", color_scheme="gray"),
                    ),
                    justify="end",
                    width="100%",
                    padding_top="8px",
                ),
                max_width="820px",
                width="90vw",
            ),
            open=PlotState.is_open,
            on_open_change=PlotState.set_is_open,
        ),
    )
