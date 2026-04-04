import reflex as rx
from ..models import GraphState as State

def upload_box():
    return rx.vstack(
        rx.upload(id="upload"),
        rx.button(
            "Upload",
            on_click=State.handle_upload(
                rx.upload_files("upload")
            ),
        ),
        rx.foreach(
            State.uploaded_files,
            lambda f: rx.image(src=rx.get_upload_url(f)),
        ),
    )