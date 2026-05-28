from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import reflex as rx


def _short_label(class_name: str) -> str:
    name = re.sub(r"^GLM", "", class_name)
    name = re.sub(r"(Transformation|Transliterator)$", "", name)
    parts = re.findall(r"[A-Z][a-z0-9]*", name)
    if not parts:
        return name[:4]
    if len(parts) == 1:
        return parts[0][:4]
    if len(parts) >= 3:
        return "".join(p[0] for p in parts)[:5]
    return parts[0][:3] + parts[1][0]


_ICONS: Dict[str, str] = {
    "GLMBinningTransformation": "bar-chart-2",
    "GLMTargetTransformation": "crosshair",
    "GLMCyclicTransformation": "rotate-cw",
    "GLMDateTransformation": "calendar",
    "GLMDateDifferenceTransformation": "calendar-minus",
    "GLMCategoryMappingTransformation": "tags",
    "GLMFeaturePairTransformation": "git-merge",
    "GLMColumnRemoverTransformation": "trash-2",
    "GLMSmartDataFilterTransformation": "filter",
    "GLMColumnNameTransliterator": "type",
    "GLMMathematicalTransformation": "sigma",
    "GLMNumericToCategoricalTransformation": "layers",
    "GLMImputationTransformation": "wand",
    "GLMTinySchemaTransformation": "split",
}


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
    def transformer_entries(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "label": _short_label(n), "icon": _ICONS.get(n, "box")}
            for n in self.transformer_names
        ]

    @rx.var
    def available_columns_hint(self) -> str:
        return ", ".join(self.available_columns)

    @rx.var
    def selected_columns_per_param(self) -> Dict[str, List[str]]:
        """For each list param, the currently selected column names parsed from value."""
        result: Dict[str, List[str]] = {}
        for p in self.param_schema:
            if p.get("is_list"):
                name = p.get("name", "")
                val = p.get("value", "")
                result[name] = [c.strip() for c in val.split(",") if c.strip()]
        return result

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
        if class_name == "GLMCategoryMappingTransformation":
            from .graph import GraphState
            from .mapping_builder_state import MappingBuilderState
            graph_state = await self.get_state(GraphState)
            yield MappingBuilderState.open_for_parent(graph_state.selected_node_id)
            return

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
                elif p["is_dict"]:
                    initial = json.dumps(default) if isinstance(default, dict) else ("" if default is None else str(default))
                else:
                    initial = "" if p["required"] else ("" if default is None else str(default))
                params.append({**p, "value": initial})
            self.param_schema = params
        else:
            self.param_schema = []

        from .auth_state import AuthState
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        cols_by_type: Optional[Dict[str, List[str]]] = pipeline_hooks.get_vertex_columns(
            session_id, parent_id
        )
        if cols_by_type:
            cols: List[str] = []
            for col_list in cols_by_type.values():
                cols.extend(col_list)
            self.available_columns = cols

        yield BusyState.hide()
        self.is_open = True

    @rx.event
    async def open_dialog_for_parent(self, node_id: str):
        """Open the config dialog using node_id as the explicit parent (add mode).

        Called from the node's '+' button so that selected_node_id is irrelevant —
        the correct parent is always the node that owns the button.
        """
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState
        from .auth_state import AuthState

        if not self.transformer_names and not pipeline_hooks.is_transformers_cached():
            yield BusyState.show("Loading transformers...")

        self.transformer_names = pipeline_hooks.available_transformers()
        self.selected_class = ""
        self.param_schema = []
        self.available_columns = []
        self.is_edit_mode = False
        self.vertex_id_editing = ""

        graph_state = await self.get_state(GraphState)
        yield graph_state._select_node(node_id)

        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        cols_by_type: Optional[Dict[str, List[str]]] = pipeline_hooks.get_vertex_columns(
            session_id, node_id
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
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        cols_by_type: Optional[Dict[str, List[str]]] = pipeline_hooks.get_vertex_columns(
            session_id, parent_id
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

            if class_name == "GLMCategoryMappingTransformation":
                from .mapping_builder_state import MappingBuilderState
                yield BusyState.hide()
                yield MappingBuilderState.open_edit_dialog(vertex_id, existing_config)
                return

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
                    elif p["is_dict"]:
                        if isinstance(existing_value, dict):
                            initial = json.dumps(existing_value)
                        elif existing_value is not None:
                            initial = str(existing_value)
                        else:
                            d = p["default"]
                            initial = json.dumps(d) if isinstance(d, dict) else ("" if d is None else str(d))
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
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        parent_id: Optional[str] = next(
            (e["source"] for e in graph_state.edges if e["target"] == vertex_id),
            None,
        )
        cols_by_type: Optional[Dict[str, List[str]]] = pipeline_hooks.get_vertex_columns(
            session_id, parent_id or vertex_id
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
    async def select_class(self, class_name: str):
        """Select a transformer class.

        When the user picks ``GLMTinySchemaTransformation``, close the generic
        config dialog and open the dedicated Tiny Schema panel instead.
        """
        if class_name == "GLMTinySchemaTransformation":
            from .graph import GraphState
            from .tiny_schema_state import TinySchemaState

            graph_state = await self.get_state(GraphState)
            parent_id = graph_state.selected_node_id
            self.is_open = False
            yield TinySchemaState.open_for_parent(parent_id)
            return

        if class_name == "GLMCategoryMappingTransformation":
            from .graph import GraphState
            from .mapping_builder_state import MappingBuilderState

            graph_state = await self.get_state(GraphState)
            parent_id = graph_state.selected_node_id
            self.is_open = False
            yield MappingBuilderState.open_for_parent(parent_id)
            return

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
            elif p["is_dict"]:
                initial = json.dumps(default) if isinstance(default, dict) else ("" if default is None else str(default))
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
    def toggle_column(self, param_name: str, col: str):
        """Add or remove col from the comma-separated value of a list param."""
        new_schema = []
        for p in self.param_schema:
            if p["name"] == param_name and p.get("is_list"):
                current = [c.strip() for c in p.get("value", "").split(",") if c.strip()]
                if col in current:
                    current.remove(col)
                else:
                    current.append(col)
                new_schema.append({**p, "value": ", ".join(current)})
            else:
                new_schema.append(p)
        self.param_schema = new_schema

    @rx.event
    async def submit(self):
        if not self.selected_class:
            return

        config: Dict[str, Any] = {}
        missing = [
            p["name"]
            for p in self.param_schema
            if p["required"] and p.get("source", "user") != "schema" and not p.get("value", "").strip()
        ]
        if missing:
            yield rx.toast.error(f"Required fields missing: {', '.join(missing)}")
            return
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
            elif p["is_dict"]:
                if raw.strip():
                    try:
                        config[name] = json.loads(raw)
                    except json.JSONDecodeError:
                        yield rx.toast.error(f"Invalid JSON for '{name}'")
                        return
                else:
                    config[name] = None if required else default
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
        graph_state = await self.get_state(GraphState)
        self.is_open = False

        if self.is_edit_mode:
            from .auth_state import AuthState
            from . import pipeline_hooks
            session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
            pipeline_hooks.update_transformation_config(
                session_id,
                self.vertex_id_editing,
                self.selected_class,
                config,
            )
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.refresh_statuses_from_pipeline()
        else:
            yield GraphState.add_transformation_node(self.selected_class, config)
