import reflex as rx


class BusyState(rx.State):
    is_busy: bool = False
    message: str = ""

    @rx.event
    def show(self, message: str):
        self.is_busy = True
        self.message = message

    @rx.event
    def hide(self):
        self.is_busy = False
        self.message = ""
