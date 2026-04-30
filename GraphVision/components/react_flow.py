import reflex as rx
from typing import Any, Dict, List

_OPEN_DIALOG_EVENT = (
    "reflex___state____state"
    ".graph_vision___models___config_state____config_state"
    ".open_dialog"
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

let __rxAddEvents = null;

const _getStatusColor = (status) => {{
  if (status === "setted")    return "#34D399";
  if (status === "fitted")    return "#3B82F6";
  if (status === "trasformed") return "#F87171";
  if (status === "complited") return "#9CA3AF";
  return "#FFFFFF";
}};

const VertexNode = ({{ data, selected }}) => {{
  const bg = selected ? "#9CA3AF" : _getStatusColor(data?.status ?? "");

  const handlePlus = (e) => {{
    e.stopPropagation();
    e.preventDefault();
    if (__rxAddEvents) {{
      __rxAddEvents([ReflexEvent("{_OPEN_DIALOG_EVENT}", {{}}, {{}})]);
    }}
  }};

  return (
    <div style={{{{
      background: bg,
      border: selected ? "2px solid #2563EB" : "1px solid #000000",
      borderRadius: "4px",
      width: "100%",
      height: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      position: "relative",
      fontSize: "12px",
      color: "#000000",
      boxSizing: "border-box",
    }}}}>
      <Handle type="target" position={{Position.Top}} />
      <span style={{{{ userSelect: "none" }}}}>{"{data?.label}"}</span>
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
          fontSize: "13px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 10,
          lineHeight: "1",
        }}}}>+</button>
      <Handle type="source" position={{Position.Bottom}} />
    </div>
  );
}};

const nodeTypes = {{ default: VertexNode }};

const ReactFlowEventBridge = () => {{
  const [addEvents] = useContext(EventLoopContext);
  useEffect(() => {{
    __rxAddEvents = addEvents;
  }}, [addEvents]);
  return null;
}};
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


class ReactFlowEventBridge(rx.Component):
    tag = "ReactFlowEventBridge"
    # Component body is injected via ReactFlow._get_custom_code()


react_flow = ReactFlow.create
background = Background.create
controls = Controls.create
node_toolbar = NodeToolbar.create
event_bridge = ReactFlowEventBridge.create
