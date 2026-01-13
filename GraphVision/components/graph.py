import reflex as rx

import random

from ..elements import button_box, button_box_drawer
from ..types import Point, Graph

class PlotState(rx.State):

    GraphPoints: Graph = Graph(points=[
        Point(x=400, y=20, label="P30"), 
        Point(x=300, y=120, label="P31"),   
    ])  

    @rx.var
    def GetPoints(self) -> list[Point]:
        return self.GraphPoints.points

    def Add(self, newlabel: str):
        self.GraphPoints.points.append(Point(x=random.randint(1, 1000), y=random.randint(1, 1000), label=newlabel))
    
    def Delete(self, label: str): 
        self.GraphPoints.points = [point for point in self.GraphPoints.points if point.label != label]

def drawer_content(label: str) -> rx.Component:
    return rx.drawer.content(
        rx.flex(
            rx.drawer.title(f"Details of {label}"),
            rx.button("Delete", width="100%", on_click=lambda: PlotState.Delete(label)),
            rx.button("Add Transformer", width="100%", on_click=lambda: PlotState.Add(f"P{random.randint(1, 1000)+1}")),
            rx.drawer.close(rx.button("Close", width="100%")),
            align_items="start",
            direction="column",
            gap="1em",
        ),
        top="auto",
        right="auto",
        height="100%",
        width="20em",
        padding="2em",
        background_color="green",
    )

def plot_layout() -> rx.Component:
    return rx.box(
        rx.foreach(
            PlotState.GetPoints,
            lambda point: button_box_drawer(point, drawer_content)
        ),
        position="absolute",
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )