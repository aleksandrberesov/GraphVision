import reflex as rx

class BoxState(rx.State):
    selected: str = ""  

    def select(self, label: str):
        self.selected = label

def drawer_content(label: str) -> rx.Component:
    return rx.drawer.content(
        rx.flex(
            rx.drawer.title(f"Details of {label}"),
            rx.button("Delete", width="100%"),
            rx.button("Add Transformer", width="100%"),
            rx.drawer.close(rx.button("Close", width="100%")),
            align_items="start",
            direction="column",
            gap="1em",
        ),
        top="auto",
        right="auto",
        height="100%",
        width="20em",
        padding="2em",
        background_color="green",
    )

def button_box(label: str, x: int, y: int) -> rx.Component:
    return rx.drawer.root(
        rx.drawer.trigger(
            rx.button(
                label,
                width="100px",
                height="100px",
                position="absolute",
                left=f"{x}px",
                top=f"{y}px",
                bg=rx.cond(BoxState.selected == label, "green", "red"),
                padding="2px",
                border_radius="4px",
                on_click=lambda: BoxState.select(label),
            )
        ),
        rx.drawer.overlay(),
        rx.drawer.portal(drawer_content(label)),
        direction="left",
        modal=True,
    )