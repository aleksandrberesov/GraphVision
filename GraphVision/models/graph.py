import reflex as rx

from ..types import Point, Graph
from .point import PointState
from ..utils import generate_random_string

from collections import defaultdict
from typing import Any, Dict, List

class GraphState(rx.State):
    selected_edge_id: rx.Var[str] = "" 
    selected_node_id: rx.Var[str] = ""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
 
    @rx.var
    def SelectedPoint(self) -> str:
        return self.selected_node_id  

    @rx.event
    def add_node(self):
        new_node_id = generate_random_string(10, use_digits=True)
        node_type = 'default'
        label = new_node_id,
        x = 0
        y = 0

        new_node = {
            'id': new_node_id,
            'type': node_type,
            'data': {'label': label},
            'position': {'x': x, 'y': y},
            'draggable': True,
        }
        self.nodes.append(new_node)

    @rx.event
    def delete_node(self, node_id: str):
        self.nodes = [node for node in self.nodes if node["id"] != node_id]
        self.edges = [
            edge for edge in self.edges
            if edge["source"] != node_id and edge["target"] != node_id
        ]

    @rx.event
    def clear_graph(self):
        self.nodes = []  
        self.edges = []  

    @rx.event
    def on_connect(self, new_edge):
        for i, edge in enumerate(self.edges):
            if edge["id"] == f"e{new_edge['source']}-{new_edge['target']}":
                del self.edges[i]
                break

        self.edges.append({
            "id": f"e{new_edge['source']}-{new_edge['target']}",
            "source": new_edge["source"],
            "target": new_edge["target"],
            "label": generate_random_string(10, use_digits=True),
            "animated": False,
        })

    @rx.event
    def on_nodes_change(self, node_changes: List[Dict[str, Any]]):
        map_id_to_new_position = defaultdict(dict)
        for change in node_changes:
            if change["type"] == "position" and change.get("dragging") == True:
                map_id_to_new_position[change["id"]] = change["position"]
            if change["type"] == "select":
                node = next((node for node in self.nodes if node["id"] == change["id"]), None)
                if node:
                    self.selected_node_id = node["id"]
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