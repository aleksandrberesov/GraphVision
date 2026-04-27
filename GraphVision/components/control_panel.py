import reflex as rx
from ..models import GraphState as State
from ..models import NodeState as Node
from .config_panel import config_panel
from .results_panel import results_panel
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
                "Create new graph",
                on_click=State.create_new_graph,
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
            rx.cond(
                (Node.id == "None") | (Node.id == None),
                rx.text("No node selected", color="red.500", font_size="sm"),
                rx.vstack(
                    rx.button(
                        "Settings",
                        on_click=Node.update_status("setted"),
                        disabled=Node.is_setted,
                        width="100%",
                    ),
                    rx.button(
                        "Fit",
                        on_click=Node.update_status("fitted"),
                        disabled=Node.is_fitted, 
                        width="100%",
                    ),
                    rx.button(
                        "Transform",
                        on_click=Node.update_status("trasformed"),
                        disabled=Node.is_trasformed, 
                        width="100%",
                    ),
                    rx.button(
                        "Add node",
                        on_click=State.add_node,
                        disabled=Node.is_complited,
                        width="100%",
                    ),
                    config_panel(),
                    results_panel(),
                    rx.button(
                        "Delete selected node",
                        on_click=State.delete_node(State.selected_node_id),
                        disabled=False,
                        width="100%",
                    ),
                    rx.cond(
                        Node.errors,
                        rx.vstack(
                            rx.text("Errors:", color="red", font_size="sm", font_weight="bold"),
                            rx.foreach(
                                Node.errors,
                                lambda e: rx.text(e, color="red", font_size="xs"),
                            ),
                            width="100%",
                            spacing="1",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    bg="lightgray",
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