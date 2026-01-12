import reflex as rx

from ..elements import labled_box, button_box, simple_box

def plot_layout(arg_points: list[dict["x": int, "y": int, "label": str]]) -> rx.Component:
    return rx.box(
        *[button_box(point["label"], point["x"], point["y"]) for point in arg_points],
 
        position="absolute",
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )
