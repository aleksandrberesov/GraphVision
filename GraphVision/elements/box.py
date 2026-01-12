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
    return rx.menu.root(
        rx.menu.trigger(
            rx.box(
            rx.text(label),
            width="100px",
            height="100px",
            position="relative",
            bg="blue",
            padding="2px",
            border_radius="4px",
            )
        ),
        rx.menu.content(
            rx.menu.item("Add Trasformer"),
            rx.menu.separator(),
            rx.menu.item("Delete"),
            rx.menu.separator(),
            rx.menu.sub(
                rx.menu.sub_trigger("More Options"),
                rx.menu.sub_content(
                    rx.menu.item("Option A"),
                    rx.menu.item("Option B"),
                ),
            ),
            side="bottom",   
            align="center", 
        ),
    )


def button_box(label: str, x: int, y: int) -> rx.Component:
    return rx.box( 
        rx.drawer.root(
            rx.drawer.trigger(
                rx.button(
                    label,
                    width="100px",
                    height="100px",
                    position="absolute",
                    left=f"{x}px",
                    top=f"{y}px",
                    bg="green",
                    padding="2px",
                    border_radius="4px",
                    on_click=lambda: BoxState.select(label),
                )
            ),
            rx.drawer.portal(
                rx.drawer.content(
                    rx.flex(
                        rx.drawer.close(rx.button("Close")),
                        rx.box(f"Details of {label}"),
                        align_items="start",
                        direction="column",
                    ),
                    top="auto",
                    right="auto",
                    height="100%",
                    width="20em",
                    padding="2em",
                    background_color="#FFF",
                )
            ),
            direction="left",
            modal=True,
        ),
    )