import reflex as rx
from typing import Any, Dict
from .graph import GraphState

class NodeState(rx.State):
    id: str | None = ""
    label: str = ""
    status: str = ""

    @rx.var
    def is_setted(self) -> bool:
        return self.status == "setted"
    
    @rx.event
    def set_status(self, status: str):
        self.status = status    

    @rx.event
    def set_node(self, node: Dict[str, Any] | None) -> None:
        if node is None:
            self.id = "None"
            self.label = "Unkhown"
        else: 
            self.id = node.get("id", "")
            self.label = node.get("data", {}).get("label", "")

    @rx.event
    def update_label(self, new_label: str):
        self.label = new_label
        return GraphState.update_node_label(self.id, new_label)    