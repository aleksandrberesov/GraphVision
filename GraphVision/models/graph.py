import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import reflex as rx

from ..utils import generate_random_string
from collections import defaultdict

untitled_name = "Untitled Graph"

class GraphState(rx.State):
    selected_edge_id: str = ""
    selected_node_id: str = ""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    title: str = ""
    uploaded_file: str = ""
    is_busy: bool = False
    busy_message: str = ""
    upload_dialog_open: bool = False
    uploaded_dataset_file: str = ""
    uploaded_schema_file: str = ""
    _next_vertex_number: int = 1
    _dataset_path: str = ""
    _schema_path: str = ""
    _dataset_ext: str = ""

    def _get_color_by_status(self, status: str) -> str:
        if status == "setted":
            return "#34D399"
        elif status == "fitted":
            return "#3B82F6"
        elif status == "trasformed":
            return "#F87171"
        elif status == "complited":
            return "#9CA3AF"
        else:
            return "#FFFFFF"

    def create_default_node(self) -> Dict[str, Any]:
        label = f"{self._next_vertex_number}."
        self._next_vertex_number += 1
        return {
            'id': generate_random_string(16, use_digits=True),
            'type': 'default',
            'data': {
                'label': label,
                'status': '',
                'transformation_class': '',
                'transformation_config': {},
            },
            'position': {
                'x': 0,
                'y': 0,
            },
            'draggable': True,
            'style': {
                'background': '#FFFFFF',
                'color': '#000000',
                'border': '1px solid #000000',
                'width': '150px',
                'height': '50px',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
            },
        }

    def _create_root_node(self, vertex_id: str) -> Dict[str, Any]:
        return {
            "id": vertex_id,
            "type": "default",
            "data": {
                "label": "Root",
                "status": "setted",
                "transformation_class": "",
                "transformation_config": {},
            },
            "position": {"x": 0, "y": 0},
            "draggable": True,
            "style": {
                "background": "#34D399",
                "color": "#000000",
                "border": "2px solid #059669",
                "width": "150px",
                "height": "50px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
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

    def _select_node(self, node_id: str):
        self.selected_node_id = node_id
        selected_node = next((node for node in self.nodes if node["id"] == node_id), None)
        from .node import NodeState
        from .plot_state import PlotState
        return [NodeState.set_node(selected_node), PlotState.load_for_node(node_id)]

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
            selected_node["style"]["background"] = self._get_color_by_status(new_status)

    @rx.event
    def set_name(self, name: str):
        self.title = name

    @rx.event
    def set_upload_dialog_open(self, value: bool):
        self.upload_dialog_open = value

    @rx.event
    def close_upload_dialog(self):
        self.upload_dialog_open = False

    @rx.event
    def save_to_file(self):
        return rx.download(
            data=json.dumps({
                "nodes": self.nodes,
                "edges": self.edges,
                "selected_node_id": self.selected_node_id,
                "selected_edge_id": self.selected_edge_id,
            }),
            filename=f"{self.title if self.title.strip() else untitled_name}.json"
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
        self.is_busy = True
        self.busy_message = "Uploading file..."
        yield
        try:
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
                    for _e in self._load_json_graph(path, file.name):
                        yield _e
                elif ext in ("csv", "parquet"):
                    self.busy_message = "Processing dataset..."
                    yield
                    from . import pipeline_hooks
                    result = pipeline_hooks.attach_data(
                        self.router.session.client_token, 
                        str(path), 
                        ext,
                        None
                    )
                    if result is not None:
                        root_vertex_id, stem = result
                        existing = next((n for n in self.nodes if n["id"] == root_vertex_id), None)
                        if existing is None:
                            self.nodes = [self._create_root_node(root_vertex_id)]
                            self.edges = []
                        else:
                            existing["data"]["label"] = stem
                        self.title = stem
                        self.nodes = pipeline_hooks.sync_statuses(
                            self.router.session.client_token, self.nodes
                        )
        finally:
            self.is_busy = False
            self.busy_message = ""

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
    async def handle_json_upload(self, files: list[rx.UploadFile]):
        self.is_busy = True
        self.busy_message = "Loading graph..."
        yield
        try:
            for file in files:
                if file.name is None:
                    continue
                data = await file.read()
                path = rx.get_upload_dir() / file.name
                with path.open("wb") as f:
                    f.write(data)
                self.uploaded_file = file.name
                ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
                if ext == "json":
                    self.upload_dialog_open = False
                    for _e in self._load_json_graph(path, file.name):
                        yield _e
        finally:
            self.is_busy = False
            self.busy_message = ""

    # ------------------------------------------------------------------
    # Node / edge operations
    # ------------------------------------------------------------------

    @rx.event
    def add_node(self):
        new_node = self.create_default_node()
        self.nodes.append(new_node)
        parent_node = next((node for node in self.nodes if node["id"] == self.selected_node_id), None)
        if parent_node is None:
            new_node["style"]["background"] = "#9CA3AF"
            return self._select_node(new_node["id"])
        else:
            self.add_edge(parent_node["id"], new_node["id"])
            self.arrange_nodes_in_row(parent_node["id"])

    @rx.event
    def delete_node(self, node_id: str):
        self.nodes = [node for node in self.nodes if node["id"] != node_id]
        self.edges = [
            edge for edge in self.edges
            if edge["source"] != node_id and edge["target"] != node_id
        ]
        return self._select_node("")

    @rx.event
    def clear_graph(self):
        self.nodes = []
        self.edges = []

    @rx.event
    async def create_new_graph(self):
        self.is_busy = True
        self.busy_message = "Creating graph..."
        yield
        try:
            self.nodes = []
            self.edges = []
            self.title = ""
            self.selected_node_id = ""
            self.selected_edge_id = ""
            self._next_vertex_number = 1

            from . import pipeline_hooks
            result = pipeline_hooks.new_pipeline(self.router.session.client_token)
            if result is not None:
                root_vertex_id, _ = result
                self.nodes.append(self._create_root_node(root_vertex_id))
                for _e in self._select_node(root_vertex_id):
                    yield _e
            else:
                self.add_node()
        finally:
            self.is_busy = False
            self.busy_message = ""

    @rx.event
    async def create_graph_with_data(self):
        if not self._dataset_path:
            return
        self.is_busy = True
        self.busy_message = "Creating graph..."
        yield
        try:
            self.nodes = []
            self.edges = []
            self.title = ""
            self.selected_node_id = ""
            self.selected_edge_id = ""
            self._next_vertex_number = 1

            from . import pipeline_hooks
            schema_path: Optional[str] = self._schema_path if self._schema_path else None
            result = pipeline_hooks.attach_data(
                self.router.session.client_token,
                self._dataset_path,
                self._dataset_ext,
                schema_path,
            )
            if result is not None:
                root_vertex_id, stem = result
                self.nodes = [self._create_root_node(root_vertex_id)]
                self.edges = []
                self.title = stem
                self.nodes = pipeline_hooks.sync_statuses(
                    self.router.session.client_token, self.nodes
                )
                for _e in self._select_node(root_vertex_id):
                    yield _e

            self._dataset_path = ""
            self._schema_path = ""
            self._dataset_ext = ""
            self.uploaded_dataset_file = ""
            self.uploaded_schema_file = ""
            self.upload_dialog_open = False
        finally:
            self.is_busy = False
            self.busy_message = ""

    @rx.event
    def on_connect(self, new_edge):
        for i, edge in enumerate(self.edges):
            if edge["id"] == f"e{new_edge['source']}-{new_edge['target']}":
                del self.edges[i]
                break
        self.add_edge(new_edge["source"], new_edge["target"])

    @rx.event
    def on_nodes_change(self, node_changes: List[Dict[str, Any]]):
        map_id_to_new_position = defaultdict(dict)
        for change in node_changes:
            if change["type"] == "position" and change.get("dragging") == True:
                map_id_to_new_position[change["id"]] = change["position"]
            if change["type"] == "select":
                node = next((node for node in self.nodes if node["id"] == change["id"]), None)
                selected_node = next((node for node in self.nodes if node["id"] == self.selected_node_id), None)
                if selected_node:
                    selected_node["style"]["background"] = self._get_color_by_status(selected_node["data"].get("status", ""))
                if node:
                    node["style"]["background"] = "#9CA3AF"
                    return self._select_node(node["id"])

        for i, node in enumerate(self.nodes):
            if node["id"] in map_id_to_new_position:
                new_position = map_id_to_new_position[node["id"]]
                self.nodes[i]["position"] = new_position

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
    def sync_from_pipeline(self):
        """Reload nodes and edges from the attached PipelineGraph."""
        from . import pipeline_hooks
        result = pipeline_hooks.pipeline_to_ui(self.router.session.client_token)
        if result is not None:
            self.nodes, self.edges = result

    @rx.event
    def refresh_statuses_from_pipeline(self):
        """Update node colours/statuses to reflect current vertex states."""
        from . import pipeline_hooks
        self.nodes = pipeline_hooks.sync_statuses(
            self.router.session.client_token, self.nodes
        )

    # ------------------------------------------------------------------
    # Pipeline operations triggered from the UI
    # ------------------------------------------------------------------

    @rx.event
    async def manifest_node(self, node_id: str):
        """Fit and apply the transformation at node_id in the pipeline."""
        self.is_busy = True
        self.busy_message = "Applying transformation..."
        yield
        try:
            from . import pipeline_hooks
            ok = pipeline_hooks.manifest_vertex(self.router.session.client_token, node_id)
            if ok:
                self.nodes = pipeline_hooks.sync_statuses(
                    self.router.session.client_token, self.nodes
                )
        finally:
            self.is_busy = False
            self.busy_message = ""

    @rx.event
    async def add_transformation_node(self, transformation_class: str, config: Dict[str, Any]):
        """Add a new node+transformation to both the UI and the pipeline."""
        self.is_busy = True
        self.busy_message = "Adding transformation..."
        yield
        try:
            parent_id = self.selected_node_id
            new_node = self.create_default_node()
            new_node["data"]["transformation_class"] = transformation_class
            new_node["data"]["transformation_config"] = config
            self.nodes.append(new_node)

            if parent_id and next((n for n in self.nodes if n["id"] == parent_id), None):
                self.add_edge(parent_id, new_node["id"])
                self.arrange_nodes_in_row(parent_id)

            from . import pipeline_hooks
            pipeline_hooks.add_transformation(
                self.router.session.client_token,
                parent_id,
                transformation_class,
                config,
                new_node["id"],
            )
            for _e in self._select_node(new_node["id"]):
                yield _e
        finally:
            self.is_busy = False
            self.busy_message = ""

    # ------------------------------------------------------------------
    # Pipeline serialisation
    # ------------------------------------------------------------------

    @rx.event
    def save_pipeline_yaml(self, path: str):
        """Save the attached PipelineGraph to a YAML file."""
        from . import pipeline_hooks
        pipeline_hooks.save_yaml(self.router.session.client_token, path)

    @rx.event
    async def load_pipeline_yaml(self, path: str):
        """Load a PipelineGraph from YAML and sync the UI."""
        self.is_busy = True
        self.busy_message = "Loading pipeline..."
        yield
        try:
            from . import pipeline_hooks
            result = pipeline_hooks.load_yaml(self.router.session.client_token, path)
            if result is not None:
                self.nodes, self.edges = result
        finally:
            self.is_busy = False
            self.busy_message = ""
