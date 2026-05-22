import reflex as rx
from typing import Any, Dict, List

_OPEN_DIALOG_FOR_PARENT_EVENT = (
    "reflex___state____state"
    ".graph_vision___models___config_state____config_state"
    ".open_dialog_for_parent"
)

class ReactFlowLib(rx.Component):
    library = "reactflow@11.10.1"

    def _get_custom_code(self) -> str:
        return """import 'reactflow/dist/style.css';"""


class ReactFlow(ReactFlowLib):
    tag = "ReactFlow"

    nodes: rx.Var[List[Dict[str, Any]]]
    edges: rx.Var[List[Dict[str, Any]]]
    fit_view: rx.Var[bool]
    nodes_draggable: rx.Var[bool]
    nodes_connectable: rx.Var[bool]
    nodes_focusable: rx.Var[bool]
    node_types: rx.Var[Any]

    on_nodes_change: rx.EventHandler[lambda e0: [e0]]
    on_edges_change: rx.EventHandler[lambda e0: [e0]]
    on_connect: rx.EventHandler[lambda e0: [e0]]

    def _get_custom_code(self) -> str:
        return f"""
import {{ Handle, Position }} from "reactflow";

const _getStatusColor = (status) => {{
  if (status === "setted")     return "#34D399";
  if (status === "fitted")     return "#3B82F6";
  if (status === "trasformed") return "#F87171";
  if (status === "complited")  return "#10B981";
  return "#9CA3AF";
}};

const _shortClass = (cls) => {{
  if (!cls) return "";
  return cls.replace(/^GLM/, "").replace(/(Transformation|Transliterator)$/, "");
}};

const VertexNode = ({{ data, id }}) => {{
  const [addEvents] = useContext(EventLoopContext);
  const bg = _getStatusColor(data?.status ?? "");
  const selected = data?.selected ?? false;
  const shortCls = _shortClass(data?.transformation_class ?? "");

  const handlePlus = (e) => {{
    e.stopPropagation();
    e.preventDefault();
    addEvents([ReflexEvent("{_OPEN_DIALOG_FOR_PARENT_EVENT}", {{"node_id": id}}, {{}})]);
  }};

  return (
    <div style={{{{
      background: bg,
      border: selected ? "3px solid #2563EB" : "1px solid #000000",
      borderRadius: "4px",
      width: "100%",
      height: "100%",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      position: "relative",
      fontSize: "12px",
      color: "#000000",
      boxSizing: "border-box",
      padding: "2px 4px",
    }}}}>
      <Handle type="target" position={{Position.Top}} />
      <span style={{{{ userSelect: "none", fontWeight: 500 }}}}>{"{data?.label}"}</span>
      {"{shortCls && ("}
        <span style={{{{ fontSize: "10px", fontWeight: 600, opacity: 0.85, userSelect: "none" }}}}>{"{shortCls}"}</span>
      {")"  + "}"}
      {"{data?.status && data.status !== '' && ("}
        <span style={{{{ fontSize: "9px", opacity: 0.6, marginTop: "1px", userSelect: "none" }}}}>{"{data.status}"}</span>
      {")"  + "}"}
      <button
        onMouseDown={{(e) => e.stopPropagation()}}
        onClick={{handlePlus}}
        title="Add transformer"
        style={{{{
          position: "absolute",
          top: "2px",
          right: "2px",
          width: "16px",
          height: "16px",
          padding: "0",
          cursor: "pointer",
          borderRadius: "50%",
          border: "1px solid #666",
          background: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 10,
        }}}}>
        <svg width="10" height="10" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg">
          <line x1="5" y1="1" x2="5" y2="9" stroke="#555" strokeWidth="1.8" strokeLinecap="round"/>
          <line x1="1" y1="5" x2="9" y2="5" stroke="#555" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
      </button>
      <Handle type="source" position={{Position.Bottom}} />
    </div>
  );
}};

const nodeTypes = {{ vertex: VertexNode }};
"""


class Background(ReactFlowLib):
    tag = "Background"
    color: rx.Var[str]
    gap: rx.Var[int]
    size: rx.Var[int]
    variant: rx.Var[str]


class Controls(ReactFlowLib):
    tag = "Controls"


class NodeToolbar(ReactFlowLib):
    tag = "NodeToolbar"
    node_id: rx.Var[str]
    is_visible: rx.Var[bool]
    position: rx.Var[str]


react_flow = ReactFlow.create
background = Background.create
controls = Controls.create
node_toolbar = NodeToolbar.create
