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
    @rx.var
    def is_fitted(self) -> bool:
        return self.status == "fitted"
    @rx.var
    def is_trasformed(self) -> bool:
        return self.status == "trasformed"
    @rx.var
    def is_complited(self) -> bool:
        return not self.status == "trasformed"
    
    @rx.event
    def update_status(self, status: str):
        self.status = status   
        return GraphState.update_node_status(self.id, status) 

    @rx.event
    def set_node(self, node: Dict[str, Any] | None) -> None:
        if node is None:
            self.id = "None"
            self.label = "Unkhown"
            self.status = ""
        else: 
            self.id = node.get("id", "")
            self.label = node.get("data", {}).get("label", "")
            self.status = node.get("data", {}).get("status", "")

    @rx.event
    def update_label(self, new_label: str):
        self.label = new_label
        return GraphState.update_node_label(self.id, new_label)    