import reflex as rx

from ..elements import button_box_drawer, button_box
from ..types import Point, Graph
from ..models import GraphState
from .react_flow_graph import graphArea

def plot_layout() -> rx.Component:
    return rx.box(
        graphArea(),
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )