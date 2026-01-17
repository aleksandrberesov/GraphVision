import reflex as rx

from .tracked_layout import tracked_layout

class MouseState(rx.State):
    x: int = 0
    y: int = 0

    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y

def layout(content: rx.Component | None = None) -> rx.Component:
    return rx.box(
        rx.text(f"Mouse X: {MouseState.x}, Y: {MouseState.y}"),
        #tracked_layout.create(onMove=MouseState.set_position), 
        content,
        position="absolute",
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )