import reflex as rx

from ..elements import selectable_boxes 

points = [
    {"x": 40, "y": 20, "label": "P1"},
    {"x": 100, "y": 60, "label": "P2"},
    {"x": 200, "y": 120, "label": "P3"},
    {"x": 300, "y": 420, "label": "P4"},
    {"x": 400, "y": 220, "label": "P5"},
]

class PlotState(rx.State):
    # Store positions of points
    points = [
        {"x": 40, "y": 20, "label": "P1"},
        {"x": 100, "y": 60, "label": "P2"},
        {"x": 200, "y": 120, "label": "P3"},
        {"x": 300, "y": 420, "label": "P4"},
        {"x": 400, "y": 220, "label": "P5"},
    ]
    selected: str = ""

    def select_point(self, label: str):
        self.selected = label
    dragging_index: int | None = None

    def start_drag(self, index: int):
        self.dragging_index = index

    def stop_drag(self):
        self.dragging_index = None

    def move_drag(self, e: rx.event):
        if self.dragging_index is not None:
            self.points[self.dragging_index]["x"] = e.client_x
            self.points[self.dragging_index]["y"] = e.client_y

def plot_layout() -> rx.Component:
    return rx.box(
        selectable_boxes(points),

        position="relative",
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )
