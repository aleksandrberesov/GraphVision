import reflex as rx
from ..models import GraphState as State
from ..models import NodeState as Node
from .upload_box import upload_box

def control_panel() -> rx.Component:
    return rx.vstack(
        rx.input(
            value=State.title,
            placeholder="enter name",
            on_change=State.set_name,   
        ),
        rx.divider(orientation="horizontal", size="4", color_scheme="blue"),
        rx.vstack(
            rx.button(
                "Clear graph",
                on_click=State.clear_graph,
                width="100%",
            ),
            rx.button(
                "Add node",
                on_click=State.add_node,
                width="100%",
            ),
            rx.button(
                "Delete selected node",
                on_click=State.delete_node(State.selected_node_id),
                width="100%",
            ),
            width="100%",
        ),
        rx.divider(orientation="horizontal", size="4", color_scheme="blue"),
        rx.vstack(
            rx.text(f"Selected Node: {Node.id}", font_size="md", font_weight="bold", color="black"),
            rx.hstack(
                rx.text(f"Title : ", font_size="md", font_weight="bold", color="black"),
                rx.input(
                    value=Node.label,
                    on_change=Node.update_label,
                    placeholder="no title",
                    color="black",
                    background_color="garis.100",  
                ),
            ),
            height="40%",
            width="100%",
            
        ),
        rx.divider(orientation="horizontal", size="4", color_scheme="blue"),
        rx.vstack(
             rx.button(
                "Download file",
                on_click=State.save_to_file,
                width="100%",
            ),
            upload_box(),
            width="100%",   
        ),
        width="100%",
        height="100%",
        border="1px solid #ccc",
        bg="white",
        spacing="4",
    )