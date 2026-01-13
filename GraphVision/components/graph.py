import reflex as rx

from ..elements import button_box
from ..types import Point, Graph

points = [
    {"x": 400, "y": 20, "label": "P1"},

]

class PlotState(rx.State):
    points: Graph = Graph(points=[])  

    def Add(self, label: str):
        self.selected = label
    
    def Delete(self, label: str):
        self.selected = ""  

def plot_layout() -> rx.Component:
    return rx.box(
        *[button_box(point["label"], point["x"], point["y"]) for point in points],
 
        position="absolute",
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )
