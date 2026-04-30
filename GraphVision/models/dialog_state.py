import reflex as rx


class DialogState(rx.State):
    create_open: bool = False
    load_open: bool = False
    save_open: bool = False
    save_filename: str = ""

    @rx.event
    def open_create(self):
        self.create_open = True

    @rx.event
    def close_create(self):
        self.create_open = False

    @rx.event
    def set_create_open(self, value: bool):
        self.create_open = value

    @rx.event
    def open_load(self):
        self.load_open = True

    @rx.event
    def close_load(self):
        self.load_open = False

    @rx.event
    def set_load_open(self, value: bool):
        self.load_open = value

    @rx.event
    async def open_save(self):
        from .graph import GraphState, untitled_name
        graph_state = await self.get_state(GraphState)
        self.save_filename = graph_state.title.strip() or untitled_name
        self.save_open = True

    @rx.event
    def close_save(self):
        self.save_open = False

    @rx.event
    def set_save_open(self, value: bool):
        self.save_open = value

    @rx.event
    def set_save_filename(self, value: str):
        self.save_filename = value

    @rx.event
    def hide(self):
        self.create_open = False
        self.load_open = False
        self.save_open = False
