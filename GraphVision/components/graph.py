import reflex as rx

from ..elements import labled_box

def plot_layout(arg_points: list[dict["x": int, "y": int, "label": str]]) -> rx.Component:
    return rx.box(
        *[labled_box(point["label"], point["x"], point["y"]) for point in arg_points],
        position="relative",
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
    )
