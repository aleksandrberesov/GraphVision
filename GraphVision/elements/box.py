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
                        
        position="relative",
        left=f"{x}px",
        top=f"{y}px",
        bg="tomato",
        padding="2px",
        border_radius="4px",

        on_click=lambda: BoxState.select(label),
    )

def simple_box(label: str, x: int, y: int) -> rx.Component:
    return rx.box(
        width="100px",
        height="100px",
        bg="blue",
        padding="2px",
        border_radius="4px",
    )

def button_box(label: str, x: int, y: int) -> rx.Component:
    return rx.button(
        label,
        width="100px",
        height="100px",
        bg="green",
        padding="2px",
        border_radius="4px",
        on_click=lambda: BoxState.select(label),
    )