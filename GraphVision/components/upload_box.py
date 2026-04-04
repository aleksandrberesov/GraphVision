import reflex as rx
from ..models import GraphState as State

color = "rgb(107,99,246)"

def upload_box():
    return rx.vstack(
        rx.upload(
            rx.icon(
                tag="cloud_upload",
                style={
                    "width": "3rem",
                    "height": "3rem",
                    "color": "#2563eb",
                    "marginBottom": "0.75rem",
                },
            ),
            rx.text(
                "Click to upload",
                style={"fontWeight": "bold", "color": "#1d4ed8"},
            ),
            id="upload",
            on_drop = State.handle_upload(),
            multiple = False,
            border="1px dotted rgb(107,99,246)",
            padding="5em",
            width="100%",
        ),
        rx.text(
            State.uploaded_file, 
            color_scheme="blue",
            width="100%",
        ),
    )