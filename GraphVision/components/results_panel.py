import reflex as rx

from ..models.plot_state import PlotState  # noqa: F401 — PlotState must be imported to register its state


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


def results_panel() -> rx.Component:
    return rx.fragment(
        rx.button(
            "View plots",
            on_click=PlotState.open_modal,
            disabled=PlotState.selected_column == "",
            width="100%",
        ),
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Data at selected node"),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("Distribution", value="dist"),
                        rx.tabs.trigger("Correlation", value="corr"),
                    ),
                    rx.tabs.content(_distribution_tab(), value="dist"),
                    rx.tabs.content(_correlation_tab(), value="corr"),
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
                max_width="680px",
                width="90vw",
            ),
            open=PlotState.is_open,
            on_open_change=PlotState.set_is_open,
        ),
    )
