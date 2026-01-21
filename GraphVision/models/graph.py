import reflex as rx

from ..types import Point, Graph
from .point import PointState

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
            last_x = parent_point.x
            new_label = f"{parent_point.label}_{'child'}_{0}"
            if parent_point.points:
                for i, child in enumerate(parent_point.points):
                    new_label = f"{parent_point.label}_{child or 'child'}_{i}"
                    #last_x = child.x
            new_point = Point(
                x=parent_point.x+10, 
                y=parent_point.y+10, 
                label=parent_point.label+"_new"
            )
            if parent_point.points is None:
                parent_point.points = []
            parent_point.points.append(new_point.label)
            self.GraphPoints.points.append(new_point)
    def Delete(self, label: str): 
        self.GraphPoints.points = [point for point in self.GraphPoints.points if point.label != label]
