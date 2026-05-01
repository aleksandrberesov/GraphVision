from __future__ import annotations

from typing import Any, Dict, List, Optional

import reflex as rx


class ConfigState(rx.State):
    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    selected_class: str = ""
    # Each item: {name, annotation, required, default, is_list, is_bool, value}
    # 'value' is always a string; list params stored as comma-separated.
    param_schema: List[Dict[str, Any]] = []
    available_columns: List[str] = []
    transformer_names: List[str] = []

    @rx.var
    def available_columns_hint(self) -> str:
        return ", ".join(self.available_columns)

    @rx.event
    async def load_transformers(self):
        """Eagerly populate transformer_names without opening the dialog."""
        from . import pipeline_hooks
        from .busy_state import BusyState
        if self.transformer_names:
            return
        if not pipeline_hooks.is_transformers_cached():
            yield BusyState.show("Loading transformers...")
        self.transformer_names = pipeline_hooks.available_transformers()
        yield BusyState.hide()

    @rx.event
    async def open_dialog_with_class(self, class_name: str):
        """Open the config dialog with class_name pre-selected (add mode)."""
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState

        if not self.transformer_names and not pipeline_hooks.is_transformers_cached():
            yield BusyState.show("Loading transformers...")

        graph_state = await self.get_state(GraphState)
        parent_id = graph_state.selected_node_id

        self.transformer_names = pipeline_hooks.available_transformers()
        self.selected_class = class_name
        self.available_columns = []
        self.is_edit_mode = False
        self.vertex_id_editing = ""

        schema = pipeline_hooks.describe_transformer(class_name)
        if schema is not None:
            params = []
            for p in schema["params"]:
                default = p["default"]
                if p["is_list"]:
                    initial = ", ".join(default) if isinstance(default, list) else ""
                elif p["is_bool"]:
                    initial = "" if p["required"] else str(default).lower()
                else:
                    initial = "" if p["required"] else ("" if default is None else str(default))
                params.append({**p, "value": initial})
            self.param_schema = params
        else:
            self.param_schema = []

        from .auth_state import AuthState
        cols_by_type: Optional[Dict[str, List[str]]] = pipeline_hooks.get_vertex_columns(
            (await self.get_state(AuthState)).user_id, parent_id
        )
        if cols_by_type:
            cols: List[str] = []
            for col_list in cols_by_type.values():
                cols.extend(col_list)
            self.available_columns = cols

        yield BusyState.hide()
        self.is_open = True

    @rx.event
    async def open_dialog(self):
        """Open the config dialog with no class pre-selected (add mode)."""
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState

        if not self.transformer_names and not pipeline_hooks.is_transformers_cached():
            yield BusyState.show("Loading transformers...")

        graph_state = await self.get_state(GraphState)
        parent_id = graph_state.selected_node_id

        self.transformer_names = pipeline_hooks.available_transformers()
        self.selected_class = ""
        self.param_schema = []
        self.available_columns = []
        self.is_edit_mode = False
        self.vertex_id_editing = ""

        from .auth_state import AuthState
        cols_by_type: Optional[Dict[str, List[str]]] = pipeline_hooks.get_vertex_columns(
            (await self.get_state(AuthState)).user_id, parent_id
        )
        if cols_by_type:
            cols: List[str] = []
            for col_list in cols_by_type.values():
                cols.extend(col_list)
            self.available_columns = cols

        yield BusyState.hide()
        self.is_open = True

    @rx.event
    async def open_edit_dialog(self):
        """Open the config dialog pre-filled with the selected vertex's existing config (edit mode)."""
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState

        if not self.transformer_names and not pipeline_hooks.is_transformers_cached():
            yield BusyState.show("Loading transformers...")

        graph_state = await self.get_state(GraphState)
        vertex_id = graph_state.selected_node_id
        if not vertex_id:
            return

        self.transformer_names = pipeline_hooks.available_transformers()

        node_data = next(
            (n["data"] for n in graph_state.nodes if n["id"] == vertex_id),
            None,
        )

        if node_data:
            class_name: str = node_data.get("transformation_class", "")
            existing_config: Dict[str, Any] = node_data.get("transformation_config", {})
            self.selected_class = class_name

            schema = pipeline_hooks.describe_transformer(class_name)
            if schema is not None:
                params = []
                for p in schema["params"]:
                    existing_value = existing_config.get(p["name"])
                    if p["is_list"]:
                        if isinstance(existing_value, list):
                            initial = ", ".join(str(v) for v in existing_value)
                        else:
                            initial = ""
                    elif p["is_bool"]:
                        if existing_value is not None:
                            initial = str(existing_value).lower()
                        else:
                            initial = "" if p["required"] else str(p["default"]).lower()
                    else:
                        if existing_value is not None:
                            initial = str(existing_value)
                        else:
                            initial = "" if p["required"] else ("" if p["default"] is None else str(p["default"]))
                    params.append({**p, "value": initial})
                self.param_schema = params
            else:
                self.param_schema = []
        else:
            self.selected_class = ""
            self.param_schema = []

        from .auth_state import AuthState
        self.available_columns = []
        cols_by_type: Optional[Dict[str, List[str]]] = pipeline_hooks.get_vertex_columns(
            (await self.get_state(AuthState)).user_id, vertex_id
        )
        if cols_by_type:
            cols: List[str] = []
            for col_list in cols_by_type.values():
                cols.extend(col_list)
            self.available_columns = cols

        self.vertex_id_editing = vertex_id
        self.is_edit_mode = True
        yield BusyState.hide()
        self.is_open = True

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value
        if not value:
            self.is_edit_mode = False
            self.vertex_id_editing = ""

    @rx.event
    def close_dialog(self):
        self.is_open = False
        self.is_edit_mode = False
        self.vertex_id_editing = ""

    @rx.event
    def select_class(self, class_name: str):
        from . import pipeline_hooks

        self.selected_class = class_name
        schema = pipeline_hooks.describe_transformer(class_name)
        if schema is None:
            self.param_schema = []
            return

        params = []
        for p in schema["params"]:
            default = p["default"]
            if p["is_list"]:
                initial = ", ".join(default) if isinstance(default, list) else ""
            elif p["is_bool"]:
                initial = "" if p["required"] else str(default).lower()
            else:
                initial = "" if p["required"] else ("" if default is None else str(default))
            params.append({**p, "value": initial})
        self.param_schema = params

    @rx.event
    def update_param(self, name: str, value: str):
        self.param_schema = [
            {**p, "value": value} if p["name"] == name else p
            for p in self.param_schema
        ]

    @rx.event
    async def submit(self):
        if not self.selected_class:
            return

        config: Dict[str, Any] = {}
        for p in self.param_schema:
            name: str = p["name"]
            ann: str = p["annotation"]
            required: bool = p["required"]
            default = p["default"]
            raw: str = p.get("value", "")

            if p["is_list"]:
                config[name] = [c.strip() for c in raw.split(",") if c.strip()]
            elif p["is_bool"]:
                config[name] = raw.lower() in ("true", "1", "yes")
            elif ann == "int":
                try:
                    config[name] = int(raw)
                except (ValueError, TypeError):
                    config[name] = default
            elif ann == "float":
                try:
                    config[name] = float(raw)
                except (ValueError, TypeError):
                    config[name] = default
            else:
                config[name] = raw if raw else (None if required else default)

        from .graph import GraphState
        self.is_open = False

        if self.is_edit_mode:
            from .auth_state import AuthState
            from . import pipeline_hooks
            pipeline_hooks.update_transformation_config(
                (await self.get_state(AuthState)).user_id,
                self.vertex_id_editing,
                self.selected_class,
                config,
            )
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            return GraphState.refresh_statuses_from_pipeline()
        else:
            return GraphState.add_transformation_node(self.selected_class, config)
