import json
from pathlib import Path

import reflex as rx

from ..utils import generate_random_string
from collections import defaultdict
from typing import Any, Dict, List

untitled_name = "Untitled Graph"

class GraphState(rx.State):
    selected_edge_id: str =  ""  
    selected_node_id: str =  ""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    title: str = ""  
    uploaded_file: str = ""

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
        return {
            'id': generate_random_string(16, use_digits=True),
            'type': 'default',
            'data': {
                'label': '',
                'status': '',
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
            selected_node["style"]["background"] = self._get_color_by_status(new_status)

    @rx.event
    def set_name(self, name: str):
        self.title = name

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

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        for file in files:
            data = await file.read()
            if file.name is None:
                continue
            path = rx.get_upload_dir() / file.name
            with path.open("wb") as f:
                f.write(data)
            self.uploaded_file = str(file.name)
            with open(path, "r") as f:
                graph_data = json.load(f)
                self.nodes = graph_data.get("nodes", [])
                self.edges = graph_data.get("edges", [])
                self.selected_edge_id = graph_data.get("selected_edge_id", "")
                self.title = file.name.rsplit(".", 1)[0]
                return self._select_node(graph_data.get("selected_node_id", ""))
            if path.exists():
                path.unlink()

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
    def create_new_graph(self):
        self.clear_graph()
        self.title = ""
        self.add_node()

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