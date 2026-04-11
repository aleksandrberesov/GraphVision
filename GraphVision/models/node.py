import reflex as rx
from typing import Any, Dict
from .graph import GraphState

class NodeState(rx.State):
    id: str | None = ""
    title: str = ""

    @rx.event
    def set_node(self, node: Dict[str, Any] | None) -> None:
        if node is None:
            self.id = "None"
            self.title = "Unkhown"
        else: 
            self.id = node.get("id", "No ID")
            self.title = node.get("title", "No Title")

    @rx.event
    def update_title(self, new_title: str):
        self.title = new_title
        GraphState.update_node_label(self.id, new_title)    