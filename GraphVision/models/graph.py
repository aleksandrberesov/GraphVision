import reflex as rx

from ..types import Point, Graph
from .point import PointState
from ..utils import generate_random_string

class GraphState(rx.State):
    selected_point: str = ""
    Points: list[PointState] = [] 
    GraphPoints: Graph = Graph(points=[
        Point(x=400, y=20, label="Start"),   
    ])  
    @rx.var
    def SelectedPoint(self) -> str:
        return self.selected_point  
    def SelectPoint(self, label: str):
        self.selected_point = label
    @rx.var
    def GetPoints(self) -> list[Point]:
        return self.GraphPoints.points
    def Add(self, point: Point):
        self.GraphPoints.points.append(point)
    def Append(self, label: str):
        parent_point = next((p for p in self.GraphPoints.points if p.label == label), None)
        if parent_point:
            new_point = Point(
                x=parent_point.x, 
                y=parent_point.y+100+10, 
                label=generate_random_string(10, use_digits=True),
                rear=parent_point.label,
            )
            self.GraphPoints.points.append(new_point)
    def Delete(self, label: str): 
        self.GraphPoints.points = [point for point in self.GraphPoints.points if point.label != label]
