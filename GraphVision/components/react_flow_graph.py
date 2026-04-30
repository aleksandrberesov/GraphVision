import reflex as rx
from .react_flow import react_flow, background, controls, event_bridge
from ..models import GraphState as State

def graphArea() -> rx.Component:
    return rx.vstack(
        react_flow(
            background(),
            controls(),
            event_bridge(),
            nodes_draggable=True,
            nodes_focusable=True,
            nodes_connectable=True,
            on_connect=lambda e0: State.on_connect(e0),
            on_nodes_change=lambda e0: State.on_nodes_change(e0),
            on_edges_change=lambda e0: State.on_edges_change(e0),
            nodes=State.nodes,
            edges=State.edges,
            fit_view=True,
            node_types=rx.Var("nodeTypes"),
        ),
        height="100%",
        width="100%",
    )

__all__ = ["graphArea"]
