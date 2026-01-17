import reflex as rx

from ..types import Point, PointPosition

class PointState(rx.State):
    x: int = 0
    y: int = 0

    @rx.var
    def Position(self) -> PointPosition:
        return PointPosition(self.x, self.y)
    def SetPosition(self, x: int, y: int):
        self.x = x
        self.y = y
    