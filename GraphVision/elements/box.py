import reflex as rx

class BoxState(rx.State):
    selected: str = ""   # store label of selected box

    def select(self, label: str):
        self.selected = label

def labled_box(label: str, x: int, y: int) -> rx.Component:
    return rx.box(
        rx.text(label),
        width=rx.cond(BoxState.selected == label, "150px", "100px"),
        height=rx.cond(BoxState.selected == label, "150px", "100px"),     
                        
        position="absolute",
        left=f"{x}px",
        top=f"{y}px",
        bg="tomato",
        padding="2px",
        border_radius="4px",

        on_click=lambda: BoxState.select(label),
    )

def selectable_boxes(arg_points: list[dict["x": int, "y": int, "label": str]]) -> rx.Component:
    return rx.box(
        rx.foreach(
            arg_points,
            lambda point: labled_box(point["label"], point["x"], point["y"]),
        ),
        position="relative",
    )