import reflex as rx
from typing import Callable
from ..types import Point

def button_box(point: Point) -> rx.Component:
    return rx.button(
        point.label,
        width="100px",
        height="100px",
        position="absolute",
        left=f"{point.x}px",
        top=f"{point.y}px",
        #bg=rx.cond(BoxState.selected == point.label, "red", "green"),
        padding="2px",
        border_radius="4px",
        #on_click=lambda: BoxState.select(point.label),
        #on_mouse_down = lambda: BoxState.start_drag,
        #on_mouse_up=DragState.stop_drag,
        #on_mouse_move=rx.event(DragState.move, args=["event.clientX", "event.clientY"]),
    )
def button_box_drawer(point: Point, drawer: Callable[[str], rx.Component] | None = None) -> rx.Component:
    return rx.drawer.root(
        rx.drawer.trigger(button_box(point)),
        rx.drawer.overlay(),
        rx.cond(drawer is not None, drawer(point.label)),    
        direction="left",
        modal=True,
    )