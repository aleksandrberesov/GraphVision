import reflex as rx

from ..elements import button_box
from ..types import Point, Graph

points = [
    {"x": 400, "y": 20, "label": "P1"},

]

class PlotState(rx.State):
    GraphPoints: Graph = Graph(points=[])  

    def GetPoints(self):
        return self.GraphPoints.points

    def Add(self, newlabel: str):
        self.GraphPoints.points.append(Point(x=50, y=50, label=newlabel))
    
    def Delete(self, label: str): 
        self.GraphPoints.points = [point for point in self.GraphPoints.points if point.label != label]

def plot_layout() -> rx.Component:
    return rx.box(
        *[button_box(point["label"], point["x"], point["y"]) for point in points],
 
        position="absolute",
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )
