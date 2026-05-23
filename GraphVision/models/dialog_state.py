from typing import List

import reflex as rx


class DialogState(rx.State):
    create_open: bool = False
    load_open: bool = False
    save_open: bool = False
    save_filename: str = ""
    download_mode: str = "structure_only"
    open_project_open: bool = False
    new_project_open: bool = False
    new_project_name: str = ""
    rename_open: bool = False
    rename_value: str = ""
    project_list: List[str] = []

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
        from .graph import GraphState
        graph_state = await self.get_state(GraphState)
        self.save_filename = graph_state.project_name
        self.download_mode = "structure_only"
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
    def set_download_mode(self, value: str):
        self.download_mode = value

    @rx.event
    async def open_project_switcher(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        user_id = (await self.get_state(AuthState)).user_id
        self.project_list = pipeline_hooks.list_projects(user_id)
        self.open_project_open = True

    @rx.event
    def set_open_project_open(self, value: bool):
        self.open_project_open = value

    @rx.event
    def open_new_project_dialog(self):
        self.new_project_name = ""
        self.new_project_open = True

    @rx.event
    def set_new_project_open(self, value: bool):
        self.new_project_open = value

    @rx.event
    def set_new_project_name(self, value: str):
        self.new_project_name = value

    @rx.event
    async def open_rename(self):
        from .graph import GraphState
        graph_state = await self.get_state(GraphState)
        self.rename_value = graph_state.project_name
        self.rename_open = True

    @rx.event
    def set_rename_open(self, value: bool):
        self.rename_open = value

    @rx.event
    def set_rename_value(self, value: str):
        self.rename_value = value

    @rx.event
    async def refresh_project_list(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        user_id = (await self.get_state(AuthState)).user_id
        if user_id:
            self.project_list = pipeline_hooks.list_projects(user_id)

    @rx.event
    async def handle_project_select_open(self, is_open: bool):
        if is_open:
            from .auth_state import AuthState
            from . import pipeline_hooks
            user_id = (await self.get_state(AuthState)).user_id
            self.project_list = pipeline_hooks.list_projects(user_id)

    @rx.event
    def hide(self):
        self.create_open = False
        self.load_open = False
        self.save_open = False
        self.open_project_open = False
        self.new_project_open = False
        self.rename_open = False
