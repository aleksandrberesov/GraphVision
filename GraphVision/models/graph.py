import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import reflex as rx

from ..utils import generate_random_string
from collections import defaultdict
from .logger_state import LoggerState

untitled_name = "Untitled Graph"

class GraphState(rx.State):
    selected_edge_id: str = ""
    selected_node_id: str = ""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    title: str = ""
    uploaded_file: str = ""
    uploaded_dataset_file: str = ""
    uploaded_schema_file: str = ""
    _next_vertex_number: int = 1
    _dataset_path: str = ""
    _schema_path: str = ""
    _dataset_ext: str = ""
    _json_path: str = ""

    json_upload: list[rx.UploadFile] = []
    data_loaded: bool = False
    project_name: str = "default"

    @rx.var
    def selected_is_root(self) -> bool:
        """True when the currently-selected node is the root (no transformation).

        Used to force Tiny Schema as the only transformer allowed directly after
        the start node.
        """
        if not self.selected_node_id:
            return False
        node = next((n for n in self.nodes if n["id"] == self.selected_node_id), None)
        if node is None:
            return False
        return node.get("data", {}).get("transformation_class", "") == ""

    def _get_color_by_status(self, status: str) -> str:
        if status == "setted":
            return "#34D399"
        elif status == "fitted":
            return "#3B82F6"
        elif status == "trasformed":
            return "#F87171"
        elif status == "complited":
            return "#10B981"
        else:
            return "#9CA3AF"

    def create_default_node(self) -> Dict[str, Any]:
        label = f"{self._next_vertex_number}."
        self._next_vertex_number += 1
        return {
            'id': generate_random_string(16, use_digits=True),
            'type': 'vertex',
            'data': {
                'label': label,
                'status': 'setted',
                'transformation_class': '',
                'transformation_config': {},
            },
            'position': {
                'x': 0,
                'y': 0,
            },
            'draggable': True,
            'style': {
                'width': '150px',
                'height': '65px',
            },
        }

    def _create_root_node(self, vertex_id: str) -> Dict[str, Any]:
        return {
            "id": vertex_id,
            "type": "vertex",
            "data": {
                "label": "Root",
                "status": "setted",
                "transformation_class": "",
                "transformation_config": {},
            },
            "position": {"x": 0, "y": 0},
            "draggable": True,
            "style": {
                "width": "150px",
                "height": "50px",
            },
        }

    def add_edge(self, source_id: str, target_id: str):
        self.edges.append({
            "id": f"e{source_id}-{target_id}",
            "source": source_id,
            "target": target_id,
            "label": "",
            "animated": False,
        })

    def arrange_nodes_in_row(self, parent_id: str):
        parent_node = next((node for node in self.nodes if node["id"] == parent_id), None)
        if parent_node is None:
            return

        child_edges = [edge for edge in self.edges if edge["source"] == parent_id]
        num_children = len(child_edges)

        if num_children == 0:
            return

        spacing = 200
        total_width = (num_children - 1) * spacing
        start_x = parent_node["position"]["x"] - total_width / 2

        for i, edge in enumerate(child_edges):
            child_node_id = edge["target"]
            child_node_index = next((index for index, node in enumerate(self.nodes) if node["id"] == child_node_id), None)
            if child_node_index is not None:
                self.nodes[child_node_index]["position"]["x"] = start_x + i * spacing
                self.nodes[child_node_index]["position"]["y"] = parent_node["position"]["y"] + 150

    def _select_node(self, node_id: str | None):
        prev = next((node for node in self.nodes if node["id"] == self.selected_node_id), None)
        if prev:
            prev["data"]["selected"] = False
        if node_id is None:
            self.selected_node_id = ""
        else:
            self.selected_node_id = node_id
        selected_node = next((node for node in self.nodes if node["id"] == node_id), None)
        if selected_node:
            selected_node["data"]["selected"] = True
        from .node import NodeState
        return NodeState.set_node(selected_node)

    @rx.event
    def update_node_label(self, node_id: str | None, new_label: str):
        selected_node = next((node for node in self.nodes if node["id"] == node_id), None)
        if selected_node:
            selected_node["data"]["label"] = new_label

    @rx.event
    def update_node_status(self, node_id: str | None, new_status: str):
        selected_node = next((node for node in self.nodes if node["id"] == node_id), None)
        if selected_node:
            selected_node["data"]["status"] = new_status

    @rx.event
    def set_name(self, name: str):
        """Legacy — kept so existing wiring doesn't break; use rename_project for real renames."""
        self.title = name

    @rx.event
    async def rename_project(self, new_name: str):
        """Rename the current project: move YAML on disk, update project_name, refresh list."""
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .dialog_state import DialogState
        new_name = new_name.strip()
        if not new_name or new_name == self.project_name:
            return
        user_id = (await self.get_state(AuthState)).user_id
        old_session = f"{user_id}::{self.project_name}"
        new_session = f"{user_id}::{new_name}"
        ok = pipeline_hooks.rename_project(old_session, new_session)
        if ok:
            old_name = self.project_name
            self.project_name = new_name
            yield DialogState.refresh_project_list
            yield rx.toast.success(f"Project renamed to '{new_name}'")
            yield LoggerState.add_log(f"Project renamed '{old_name}' → '{new_name}'", "success")
        else:
            yield rx.toast.error(f"Cannot rename: '{new_name}' already exists")

    @rx.event
    async def download_project(self):
        """Export the full project to a YAML file and trigger browser download."""
        from .auth_state import AuthState
        from .busy_state import BusyState
        from .dialog_state import DialogState
        from . import pipeline_hooks
        dialog_state = await self.get_state(DialogState)
        name = dialog_state.save_filename.strip() or self.project_name
        mode = dialog_state.download_mode
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{self.project_name}"
        yield DialogState.hide()
        yield BusyState.show("Preparing download…")
        try:
            yaml_str = pipeline_hooks.export_project_yaml(
                session_id, self.nodes, self.edges, name, mode
            )
        finally:
            yield BusyState.hide()
        yield rx.download(data=yaml_str, filename=f"{name}.yaml")
        yield LoggerState.add_log(f"Project downloaded as '{name}.yaml' [{mode}]", "success")

    @rx.event
    async def export_branch_pipeline(self):
        """Serialize the selected branch's fitted sklearn Pipeline and download it."""
        from .auth_state import AuthState
        from .busy_state import BusyState
        from . import pipeline_hooks
        vertex_id = self.selected_node_id
        if not vertex_id:
            yield rx.toast.error("Select a fitted model node first")
            return
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{self.project_name}"
        yield BusyState.show("Building pipeline…")
        try:
            data = pipeline_hooks.export_pipeline(session_id, vertex_id)
        finally:
            yield BusyState.hide()
        if data is None:
            yield rx.toast.error(
                "Pipeline export failed — ensure the model node is fitted. "
                "Check logs for details."
            )
            return
        filename = f"{self.project_name}_{vertex_id}_pipeline.pkl"
        yield rx.download(data=data, filename=filename)
        yield LoggerState.add_log(
            f"Pipeline exported as '{filename}'", "success"
        )

    # ------------------------------------------------------------------
    # Upload handling
    # ------------------------------------------------------------------

    def _load_json_graph(self, path: Path, file_name: str):
        with open(path, "r") as f:
            graph_data = json.load(f)
        self.nodes = graph_data.get("nodes", [])
        self.edges = graph_data.get("edges", [])
        self.selected_edge_id = graph_data.get("selected_edge_id", "")
        self.title = file_name.rsplit(".", 1)[0]
        path.unlink(missing_ok=True)
        return self._select_node(graph_data.get("selected_node_id", ""))

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        from .auth_state import AuthState
        from .busy_state import BusyState
        yield BusyState.show("Uploading file...")
        try:
            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            for file in files:
                data = await file.read()
                if file.name is None:
                    continue
                path = rx.get_upload_dir() / file.name
                with path.open("wb") as f:
                    f.write(data)
                self.uploaded_file = str(file.name)
                ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
                if ext == "json":
                    self._load_json_graph(path, file.name)
                    yield LoggerState.add_log(f"Graph loaded from '{file.name}'", "success")

                elif ext in ("csv", "parquet"):
                    yield BusyState.show("Processing dataset...")
                    from . import pipeline_hooks
                    # Loading a dataset starts a fresh graph. The previous graph's
                    # downstream transformers were built for the OLD dataset's
                    # columns, so reusing the existing pipeline leaves stale
                    # vertices behind: analytics shows the old cached frames and
                    # data preview fails to re-manifest against the new columns
                    # ("no dataset"). Reset the backend to a clean root first, and
                    # always rebuild the UI as a single root node.
                    pipeline_hooks.new_pipeline(session_id)
                    result = pipeline_hooks.attach_data(
                        session_id,
                        str(path),
                        ext,
                        None
                    )
                    if result is not None:
                        root_vertex_id, stem = result
                        self.nodes = [self._create_root_node(root_vertex_id)]
                        self.edges = []
                        self.title = stem
                        self.data_loaded = True
                        self.nodes = pipeline_hooks.sync_statuses(
                            session_id, self.nodes
                        )
                        pipeline_hooks.persist_pipeline(session_id)
                        yield self._select_node(root_vertex_id)
                        yield LoggerState.add_log(f"Dataset '{file.name}' attached", "success")
                    else:
                        yield LoggerState.add_log(f"Failed to attach dataset '{file.name}'", "error")
        finally:
            yield BusyState.hide()

    @rx.event
    async def handle_dataset_upload(self, files: list[rx.UploadFile]):
        for file in files:
            if file.name is None:
                continue
            ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
            if ext not in ("csv", "parquet"):
                continue
            data = await file.read()
            path = rx.get_upload_dir() / file.name
            with path.open("wb") as f:
                f.write(data)
            self._dataset_path = str(path)
            self._dataset_ext = ext
            self.uploaded_dataset_file = file.name
            yield LoggerState.add_log(f"Dataset '{file.name}' staged", "info")

    @rx.event
    async def handle_schema_upload(self, files: list[rx.UploadFile]):
        for file in files:
            if file.name is None:
                continue
            ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
            if ext not in ("json", "yaml", "yml"):
                continue
            data = await file.read()
            path = rx.get_upload_dir() / file.name
            with path.open("wb") as f:
                f.write(data)
            self._schema_path = str(path)
            self.uploaded_schema_file = file.name

    @rx.event
    def clear_staged_yaml(self):
        """Discard a staged YAML file (e.g. when the user cancels the rename dialog)."""
        self._json_path = ""
        self.uploaded_file = ""

    @rx.event
    async def handle_yaml_stage(self, files: list[rx.UploadFile]):
        """Stage a .yaml/.yml project file for import (stores path, shows filename)."""
        for file in files:
            if file.name is None:
                continue
            ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
            if ext not in ("yaml", "yml"):
                continue
            data = await file.read()
            path = rx.get_upload_dir() / file.name
            with path.open("wb") as f:
                f.write(data)
            self._json_path = str(path)
            self.uploaded_file = file.name

    @rx.event
    async def handle_yaml_upload(self):
        """Import a staged project YAML: reconstruct pipeline + UI, register project."""
        from .auth_state import AuthState
        from .busy_state import BusyState
        from .dialog_state import DialogState
        from . import pipeline_hooks
        if not self._json_path:
            return
        yield BusyState.show("Importing project…")
        user_id = (await self.get_state(AuthState)).user_id
        existing = pipeline_hooks.list_projects(user_id)
        with open(self._json_path, "rb") as fh:
            yaml_bytes = fh.read()
        # Peek at project_name to check for name conflict before full parse
        try:
            import yaml as _yaml
            peek = _yaml.safe_load(yaml_bytes) or {}
            incoming_name: str = peek.get("project_name", "imported-project")
        except Exception:
            incoming_name = "imported-project"
        if incoming_name in existing:
            # Name conflict — ask the user to pick a different name via dialog
            yield BusyState.hide()
            yield DialogState.hide()
            yield DialogState.open_import_rename(incoming_name)
            return
        for _e in self._do_import(user_id, yaml_bytes):
            yield _e

    @rx.event
    async def handle_yaml_upload_with_override(self):
        """Confirm import using the name chosen in the import-rename dialog."""
        from .auth_state import AuthState
        from .busy_state import BusyState
        from .dialog_state import DialogState
        from . import pipeline_hooks
        dialog_state = await self.get_state(DialogState)
        override_name = dialog_state.import_rename_value.strip()
        if not override_name or not self._json_path:
            return
        user_id = (await self.get_state(AuthState)).user_id
        existing = pipeline_hooks.list_projects(user_id)
        if override_name in existing:
            yield rx.toast.error(
                f"Project '{override_name}' already exists — choose a different name"
            )
            return
        yield BusyState.show("Importing project…")
        with open(self._json_path, "rb") as fh:
            yaml_bytes = fh.read()
        for _e in self._do_import(user_id, yaml_bytes, name_override=override_name):
            yield _e

    def _do_import(self, user_id: str, yaml_bytes: bytes, name_override: str = ""):
        """Shared import logic used by both upload paths. Yields Reflex events."""
        from .busy_state import BusyState
        from .dialog_state import DialogState
        from . import pipeline_hooks
        try:
            session_id = f"{user_id}::__import__"
            result = pipeline_hooks.import_project_yaml(
                session_id, yaml_bytes, name_override or None
            )
            if result is None:
                yield rx.toast.error("Failed to import — invalid project YAML")
                return
            project_name, nodes, edges = result
            self.project_name = project_name
            self.nodes = nodes
            self.edges = edges
            self.data_loaded = True
            self._json_path = ""
            self.uploaded_file = ""
            yield DialogState.refresh_project_list
            yield rx.toast.success(f"Project '{project_name}' imported")
            yield LoggerState.add_log(f"Project '{project_name}' imported from YAML", "success")
        finally:
            yield BusyState.hide()
            yield DialogState.hide()

    # ------------------------------------------------------------------
    # Node / edge operations
    # ------------------------------------------------------------------

    @rx.event
    def create_root(self):
        new_node = self.create_default_node()
        self.nodes.append(new_node)
        yield self._select_node(new_node["id"])
        yield LoggerState.add_log(f"Root node '{new_node['data']['label']}' added", "info")

    @rx.event
    async def delete_node(self, node_id: str):
        from .auth_state import AuthState
        from . import pipeline_hooks
        node = next((n for n in self.nodes if n["id"] == node_id), None)
        label = node["data"]["label"] if node else node_id
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{self.project_name}"
        result = pipeline_hooks.delete_vertex(session_id, node_id)
        if result is not None:
            # Backend did the deletion + cascade + orphan pruning; trust it.
            self.nodes, self.edges = result
        else:
            # No backend connected, or root was attempted — fall back to
            # local-only removal (keeps the UI consistent in dev/test mode).
            self.nodes = [n for n in self.nodes if n["id"] != node_id]
            self.edges = [
                e for e in self.edges
                if e["source"] != node_id and e["target"] != node_id
            ]
        yield self._select_node("")
        yield LoggerState.add_log(f"Node '{label}' deleted", "warning")

    @rx.event
    def clear_graph(self):
        self.nodes = []
        self.edges = []
        yield LoggerState.add_log("Graph cleared", "warning")

    @rx.event
    async def create_new_graph(self):
        from .auth_state import AuthState
        from .busy_state import BusyState
        root_vertex_id = ""
        yield BusyState.show("Creating graph...")
        try:
            self.nodes = []
            self.edges = []
            self.title = ""
            self.selected_node_id = ""
            self.selected_edge_id = ""
            self._next_vertex_number = 1

            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            from . import pipeline_hooks
            result = pipeline_hooks.new_pipeline(session_id)
            if result is not None:
                root_vertex_id, _ = result
                self.nodes.append(self._create_root_node(root_vertex_id))
            else:
                self.create_root()
        finally:
            yield BusyState.hide()
            yield self._select_node(root_vertex_id)
            yield LoggerState.add_log("New empty graph created", "success")

    @rx.event
    async def create_graph_with_data(self):
        root_vertex_id = ""
        schema_was_provided = False  # safe default for the finally block

        from .auth_state import AuthState
        from .busy_state import BusyState
        if not self._dataset_path:
            return
        yield BusyState.show("Creating graph...")
        try:
            self.nodes = []
            self.edges = []
            self.title = ""
            self.selected_node_id = ""
            self.selected_edge_id = ""
            self._next_vertex_number = 1

            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            from . import pipeline_hooks
            # Start from a clean backend pipeline so a project_name that collides
            # with a previous session can't leave stale downstream vertices behind
            # (they were built for the old dataset's columns).
            pipeline_hooks.new_pipeline(session_id)
            schema_path: Optional[str] = self._schema_path if self._schema_path else None
            result = pipeline_hooks.attach_data(
                session_id,
                self._dataset_path,
                self._dataset_ext,
                schema_path,
            )
            if result is not None:
                root_vertex_id, stem = result
                self.nodes = [self._create_root_node(root_vertex_id)]
                self.edges = []
                self.title = stem
                self.data_loaded = True
                self.nodes = pipeline_hooks.sync_statuses(
                    session_id, self.nodes
                )

            pipeline_hooks.persist_pipeline(session_id)

            schema_was_provided = bool(schema_path)
            self._dataset_path = ""
            self._schema_path = ""
            self._dataset_ext = ""
            self.uploaded_dataset_file = ""
            self.uploaded_schema_file = ""
        finally:
            from .dialog_state import DialogState
            from .schema_state import BaseSchemaState
            yield DialogState.hide()
            yield BusyState.hide()
            yield self._select_node(root_vertex_id)
            yield LoggerState.add_log(f"Graph created with dataset '{self.title}'", "success")

    @rx.event
    def on_connect(self, new_edge):
        for i, edge in enumerate(self.edges):
            if edge["id"] == f"e{new_edge['source']}-{new_edge['target']}":
                del self.edges[i]
                break
        self.add_edge(new_edge["source"], new_edge["target"])
        src = next((n["data"]["label"] for n in self.nodes if n["id"] == new_edge["source"]), new_edge["source"])
        tgt = next((n["data"]["label"] for n in self.nodes if n["id"] == new_edge["target"]), new_edge["target"])
        yield LoggerState.add_log(f"Edge connected: '{src}' → '{tgt}'", "info")

    @rx.event
    def on_nodes_change(self, node_changes: List[Dict[str, Any]]):
        map_id_to_new_position = defaultdict(dict)
        for change in node_changes:
            if change["type"] == "position" and change.get("dragging") == True:
                map_id_to_new_position[change["id"]] = change["position"]
                for i, node in enumerate(self.nodes):
                    if node["id"] in map_id_to_new_position:
                        new_position = map_id_to_new_position[node["id"]]
                        self.nodes[i]["position"] = new_position
            if change["type"] == "select":
                node = next((node for node in self.nodes if node["id"] == change["id"]), None)
                if node:
                    return self._select_node(node["id"])

    @rx.event
    def on_edges_change(self, edge_changes: List[Dict[str, Any]]):
        for change in edge_changes:
            if change["type"] == "select":
                edge = next((edge for edge in self.edges if edge["id"] == change["id"]), None)
                if edge:
                    self.selected_edge_id = edge["id"]

    # ------------------------------------------------------------------
    # Pipeline sync events (UI ← pipeline)
    # ------------------------------------------------------------------

    @rx.event
    async def restore_session(self):
        """On page load: reload nodes/edges from memory or disk for the current user.

        All state mutations are accumulated synchronously before any yield so
        that the client receives a single coherent delta: data_loaded=True and
        constructor_open=True (when applicable) arrive together.  Splitting
        them across multiple yields caused intermediate states where
        data_loaded=False was visible while the constructor was open, letting
        users accidentally open the "Create graph" dialog on top.
        """
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .dialog_state import DialogState

        user_id = (await self.get_state(AuthState)).user_id
        if not user_id:
            return

        # Fast-path: Reflex state survives WebSocket reconnects server-side.
        # If data_loaded is already True the graph is already in a good state
        # (e.g. we're on a post-upload reconnect).  Skip the restore to avoid
        # re-rendering the whole graph and emitting a spurious "Session
        # restored" log that looks like a page reload.
        if self.data_loaded:
            return

        session_id = f"{user_id}::{self.project_name}"
        result = pipeline_hooks.restore_pipeline(session_id)
        restored_msg = ""
        if result is not None:
            self.nodes, self.edges = result
            self.data_loaded = True
            restored_msg = f"Session restored — project '{self.project_name}'"


        # First yield: sends the entire accumulated delta in one packet.
        if restored_msg:
            yield LoggerState.add_log(restored_msg, "info")
        yield DialogState.refresh_project_list

    @rx.event
    async def sync_from_pipeline(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
        result = pipeline_hooks.pipeline_to_ui(session_id)
        if result is not None:
            self.nodes, self.edges = result
            self.data_loaded = True

    @rx.event
    async def refresh_statuses_from_pipeline(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
        self.nodes = pipeline_hooks.sync_statuses(session_id, self.nodes)

    # ------------------------------------------------------------------
    # Pipeline operations triggered from the UI
    # ------------------------------------------------------------------

    @rx.event
    async def manifest_node(self, node_id: str):
        from .auth_state import AuthState
        from .busy_state import BusyState
        yield BusyState.show("Applying transformation...")
        try:
            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            from . import pipeline_hooks
            error = pipeline_hooks.manifest_vertex(session_id, node_id)
            for entry in pipeline_hooks.pending_logs:
                yield LoggerState.add_log(entry["message"], entry["level"])
            pipeline_hooks.pending_logs = []
            self.nodes = pipeline_hooks.sync_statuses(session_id, self.nodes)
            from .node import NodeState
            updated_node = next((n for n in self.nodes if n["id"] == node_id), None)
            yield NodeState.set_node(updated_node)
            pipeline_hooks.persist_pipeline(session_id)
            node_label = next((n["data"]["label"] for n in self.nodes if n["id"] == node_id), node_id)
            if error is None:
                yield rx.toast.success("Applied!")
                yield LoggerState.add_log(f"Node '{node_label}' applied successfully", "success")
            else:
                yield rx.toast.error(error)
                yield LoggerState.add_log(f"Node '{node_label}' failed: {error}", "error")
        finally:
            yield BusyState.hide()

    @rx.event
    async def apply_config_edit(self, vertex_id: str, class_name: str, config: Dict[str, Any]):
        """Update an existing vertex's config, re-apply it, and persist."""
        from .auth_state import AuthState
        from .busy_state import BusyState
        from . import pipeline_hooks
        yield BusyState.show("Applying transformation...")
        try:
            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            pipeline_hooks.update_transformation_config(session_id, vertex_id, class_name, config)
            # Keep UI node data in sync so edit dialog reopens with new values.
            self.nodes = [
                {**n, "data": {**n["data"], "transformation_config": config}}
                if n["id"] == vertex_id else n
                for n in self.nodes
            ]
            error = pipeline_hooks.manifest_vertex(session_id, vertex_id)
            for entry in pipeline_hooks.pending_logs:
                yield LoggerState.add_log(entry["message"], entry["level"])
            pipeline_hooks.pending_logs = []
            self.nodes = pipeline_hooks.sync_statuses(session_id, self.nodes)
            from .node import NodeState
            updated_node = next((n for n in self.nodes if n["id"] == vertex_id), None)
            yield NodeState.set_node(updated_node)
            pipeline_hooks.persist_pipeline(session_id)
            if error is None:
                yield rx.toast.success("Transformer updated!")
                yield LoggerState.add_log(f"Transformer '{class_name}' reconfigured and applied", "success")
            else:
                yield rx.toast.error(error)
                yield LoggerState.add_log(f"Transformer '{class_name}' reconfigured but failed: {error}", "error")
        finally:
            yield BusyState.hide()

    @rx.event
    async def add_transformation_node(self, transformation_class: str, config: Dict[str, Any]):
        import asyncio
        from .auth_state import AuthState
        from .busy_state import BusyState
        new_node = self.create_default_node()
        yield BusyState.show("Adding transformation...")
        await asyncio.sleep(0.05)
        try:
            parent_id = self.selected_node_id
            new_node["data"]["transformation_class"] = transformation_class
            new_node["data"]["transformation_config"] = config
            self.nodes.append(new_node)

            if parent_id and next((n for n in self.nodes if n["id"] == parent_id), None):
                self.add_edge(parent_id, new_node["id"])
                self.arrange_nodes_in_row(parent_id)

            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            from . import pipeline_hooks
            print(f"[UI] add_transformation_node: session_id={session_id}, parent_id={parent_id}, class={transformation_class}")
            registered_id = pipeline_hooks.add_transformation(
                session_id,
                parent_id,
                transformation_class,
                config,
                new_node["id"],
            )
            for entry in pipeline_hooks.pending_logs:
                yield LoggerState.add_log(entry["message"], entry["level"])
            pipeline_hooks.pending_logs = []
            if registered_id is None:
                self.nodes = [n for n in self.nodes if n["id"] != new_node["id"]]
                self.edges = [
                    e for e in self.edges
                    if e["source"] != new_node["id"] and e["target"] != new_node["id"]
                ]
                
                # Check if pipeline exists to give a better error
                from . import pipeline_hooks
                if not pipeline_hooks.get_pipeline(session_id):
                    yield rx.toast.error("Failed to add transformer — no dataset loaded?")
                    yield LoggerState.add_log(f"Failed to add '{transformation_class}' — no dataset loaded", "error")
                else:
                    yield rx.toast.error(f"Failed to add '{transformation_class}' — internal error. Check logs.")
                    yield LoggerState.add_log(f"Failed to add '{transformation_class}' — hook returned None", "error")
                return

            pipeline_hooks.persist_pipeline(session_id)
            yield LoggerState.add_log(f"Transformer '{transformation_class}' added", "info")

        finally:
            yield BusyState.hide()
            # Only select the new node if it still exists (wasn't rolled back)
            if any(n["id"] == new_node["id"] for n in self.nodes):
                yield self._select_node(new_node["id"])

    @rx.event
    async def add_model_node(self, parent_id: str, family: str, link: str):
        """Add a GLM model vertex as a child of parent_id and select it."""
        import asyncio
        from .auth_state import AuthState
        from .busy_state import BusyState
        from .logger_state import LoggerState

        new_node = self.create_default_node()
        yield BusyState.show("Adding model node…")
        await asyncio.sleep(0.05)
        try:
            new_node["data"]["transformation_class"] = "GLMModelEstimator"
            new_node["data"]["transformation_config"] = {"family": family, "link": link}
            new_node["data"]["node_type"] = "model"
            self.nodes.append(new_node)

            if parent_id and next((n for n in self.nodes if n["id"] == parent_id), None):
                self.add_edge(parent_id, new_node["id"])
                self.arrange_nodes_in_row(parent_id)

            from . import pipeline_hooks
            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            registered_id = pipeline_hooks.add_model_node(
                session_id, parent_id, family, link, new_node["id"]
            )
            for entry in pipeline_hooks.pending_logs:
                yield LoggerState.add_log(entry["message"], entry["level"])
            pipeline_hooks.pending_logs = []

            if registered_id is None:
                self.nodes = [n for n in self.nodes if n["id"] != new_node["id"]]
                self.edges = [
                    e for e in self.edges
                    if e["source"] != new_node["id"] and e["target"] != new_node["id"]
                ]
                yield rx.toast.error("Failed to add model node — no dataset loaded?")
                yield LoggerState.add_log("Failed to add GLM model node", "error")
                return

            pipeline_hooks.persist_pipeline(session_id)
            yield LoggerState.add_log(f"Model node added (family={family}, link={link})", "info")

        finally:
            yield BusyState.hide()
            if any(n["id"] == new_node["id"] for n in self.nodes):
                yield self._select_node(new_node["id"])

    @rx.event
    async def add_model_flow(
        self, parent_id: str, kept_columns: List[str], family: str, link: str
    ):
        """Option-A model flow — insert ColumnRemover → hidden Transliterator →
        model upstream of parent_id in one backend action and adopt the fresh
        graph (BFS-laid-out, same pattern as delete)."""
        from .auth_state import AuthState
        from .busy_state import BusyState
        from .logger_state import LoggerState
        from . import pipeline_hooks

        yield BusyState.show("Building model flow…")
        try:
            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            result = pipeline_hooks.add_model_flow(
                session_id, parent_id, kept_columns, family, link
            )
            for entry in pipeline_hooks.pending_logs:
                yield LoggerState.add_log(entry["message"], entry["level"])
            pipeline_hooks.pending_logs = []

            if not result:
                yield rx.toast.error("Failed to add model flow — check logs.")
                yield LoggerState.add_log("add_model_flow returned None", "error")
                return

            self.nodes = result["nodes"]
            self.edges = result["edges"]
            pipeline_hooks.persist_pipeline(session_id)
            yield LoggerState.add_log(
                f"Model flow added (drop unselected → transliterate → "
                f"GLM family={family}, link={link})", "info",
            )
            model_id = result.get("model_id", "")
            if model_id:
                yield self._select_node(model_id)
        finally:
            yield BusyState.hide()

    # ------------------------------------------------------------------
    # Multi-project support
    # ------------------------------------------------------------------

    @rx.event
    async def switch_project(self, name: str):
        """Save current pipeline, then load the named project for this user."""
        from .auth_state import AuthState
        from .busy_state import BusyState
        from . import pipeline_hooks
        user_id = (await self.get_state(AuthState)).user_id
        if not user_id or not name:
            return
        pipeline_hooks.persist_pipeline(f"{user_id}::{self.project_name}")
        self.project_name = name
        yield BusyState.show(f"Opening project '{name}'…")
        try:
            result = pipeline_hooks.restore_pipeline(f"{user_id}::{name}")
            if result is not None:
                self.nodes, self.edges = result
                self.data_loaded = True
            else:
                self.nodes = []
                self.edges = []
                self.data_loaded = False
                self.title = ""
            yield LoggerState.add_log(f"Switched to project '{name}'", "info")
        finally:
            yield BusyState.hide()

    @rx.event
    async def new_project(self, name: str):
        """Save current pipeline and start a blank project with the given name."""
        from .auth_state import AuthState
        from .busy_state import BusyState
        from . import pipeline_hooks
        user_id = (await self.get_state(AuthState)).user_id
        if not user_id or not name:
            return
        saved_name = self.project_name
        pipeline_hooks.persist_pipeline(f"{user_id}::{saved_name}")
        self.project_name = name
        self.nodes = []
        self.edges = []
        self.data_loaded = False
        self.title = ""
        self.selected_node_id = ""
        self.selected_edge_id = ""
        self._next_vertex_number = 1
        yield rx.toast.success(f"Project '{saved_name}' saved. Starting '{name}'…", duration=4000)
        yield LoggerState.add_log(f"Project '{saved_name}' saved. New project '{name}' created", "success")
        from .dialog_state import DialogState
        yield DialogState.refresh_project_list

    # ------------------------------------------------------------------
    # Pipeline serialisation
    # ------------------------------------------------------------------

    @rx.event
    async def save_pipeline_yaml(self, path: str):
        from .auth_state import AuthState
        from . import pipeline_hooks
        session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
        pipeline_hooks.save_yaml(session_id, path)

    @rx.event
    async def load_pipeline_yaml(self, path: str):
        from .auth_state import AuthState
        from .busy_state import BusyState
        yield BusyState.show("Loading pipeline...")
        try:
            session_id = f"{(await self.get_state(AuthState)).user_id}::{self.project_name}"
            from . import pipeline_hooks
            result = pipeline_hooks.load_yaml(session_id, path)
            if result is not None:
                self.nodes, self.edges = result
                self.data_loaded = True
                yield LoggerState.add_log(f"Pipeline loaded from '{path}'", "success")
        finally:
            yield BusyState.hide()
