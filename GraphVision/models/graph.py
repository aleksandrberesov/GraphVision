import reflex as rx

from ..types import Point, Graph

class GraphState(rx.State):

    GraphPoints: Graph = Graph(points=[
        Point(x=400, y=20, label="P30"),   
    ])  

    @rx.var
    def GetPoints(self) -> list[Point]:
        return self.GraphPoints.points

    def Append(self, label: str):
        point = next((p for p in self.GraphPoints.points if p.label == label), None)
        self.GraphPoints.points.append(Point(x=point.x+10, y=point.y+10, label=point.label+"_copy"))
    def Delete(self, label: str): 
        self.GraphPoints.points = [point for point in self.GraphPoints.points if point.label != label]
