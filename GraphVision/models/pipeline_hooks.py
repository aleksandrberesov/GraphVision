"""
Pipeline hook slots — the only coupling point between GraphVision and any
external pipeline backend.

Every slot is a plain callable with a no-op default.  A bridge layer (or test
fixture) replaces the defaults at process startup by assigning to these names
directly:

    from GraphVision.models import pipeline_hooks
    pipeline_hooks.get_pipeline = my_impl

GraphVision itself never imports axiolyze or bridge_layer.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Registry access
# ---------------------------------------------------------------------------

# (session_id: str) -> Optional[Any]
# Return the PipelineGraph for this session, or None.
get_pipeline: Callable[[str], Optional[Any]] = lambda _: None

# (session_id: str) -> Optional[Tuple[str, Any]]
# Create a new empty pipeline, register it, return (root_vertex_id, pipeline).
new_pipeline: Callable[[str], Optional[Tuple[str, Any]]] = lambda _: None


# ---------------------------------------------------------------------------
# UI synchronisation  (pipeline state → GraphState nodes/edges)
# ---------------------------------------------------------------------------

# (session_id: str) -> Optional[Tuple[List[Dict], List[Dict]]]
# Convert the full pipeline to (nodes, edges) for ReactFlow.
# Returns None if no pipeline is attached to the session.
pipeline_to_ui: Callable[
    [str], Optional[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]
] = lambda _: None

# (session_id: str, nodes: List[Dict]) -> List[Dict]
# Return a new nodes list with status/colour updated from pipeline vertex states.
# Falls back to returning the original list unchanged.
sync_statuses: Callable[
    [str, List[Dict[str, Any]]], List[Dict[str, Any]]
] = lambda _, nodes: nodes


# ---------------------------------------------------------------------------
# Data attachment
# ---------------------------------------------------------------------------

# (session_id: str, file_path: str, ext: str, schema_path: Optional[str]) -> Optional[Tuple[str, str]]
# Load a data file (csv/parquet), optionally apply a pre-built schema, attach to pipeline.
# Returns (root_vertex_id, file_stem) on success, None on failure or if
# no implementation is registered.
attach_data: Callable[
    [str, str, str, Optional[str]], Optional[Tuple[str, str]]
] = lambda *_: None


# ---------------------------------------------------------------------------
# Pipeline operations
# ---------------------------------------------------------------------------

# (session_id: str, node_id: str) -> Optional[str]
# Fit and apply the transformation at node_id.
# Returns None on success, or an error message string on failure.
manifest_vertex: Callable[[str, str], Optional[str]] = lambda *_: "No backend connected"

# (session_id: str, parent_id: str, class_name: str, config: Dict, ui_node_id: str) -> Optional[str]
# Add a transformation to the pipeline.  Returns the vertex_id used (may equal
# ui_node_id if the backend preserved it), or None on failure.
add_transformation: Callable[
    [str, str, str, Dict[str, Any], str], Optional[str]
] = lambda *_: None

# (session_id: str, path: str) -> None
save_yaml: Callable[[str, str], None] = lambda *_: None

# (session_id: str, path: str) -> Optional[Tuple[List[Dict], List[Dict]]]
# Load a pipeline from YAML, register it, return (nodes, edges).
load_yaml: Callable[
    [str, str], Optional[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]
] = lambda *_: None

# () -> List[str]
# Return sorted list of registered transformer class names.
available_transformers: Callable[[], List[str]] = lambda: []

# () -> bool
# Return True if the transformer registry is already built (no I/O needed).
is_transformers_cached: Callable[[], bool] = lambda: False

# (class_name: str) -> Optional[Dict[str, Any]]
# Return the param schema for a transformer's __init__.  Shape:
#   {"class_name": str, "params": [{"name", "annotation", "required", "default", "is_list", "is_bool"}, …]}
describe_transformer: Callable[[str], Optional[Dict[str, Any]]] = lambda _: None

# (session_id: str, vertex_id: str) -> Optional[Dict[str, List[str]]]
# Return visible column names grouped by type for a manifested vertex.
# Returns None if vertex not found or not yet manifested.
get_vertex_columns: Callable[[str, str], Optional[Dict[str, List[str]]]] = lambda *_: None

# (session_id: str, vertex_id: str, column: str) -> Optional[Dict[str, Any]]
# Compute or retrieve cached distribution for a column at a vertex.
# Result keys: histogram (List[float]), kde (optional), statistics (Dict).
compute_distribution: Callable[[str, str, str], Optional[Dict[str, Any]]] = lambda *_: None

# (session_id: str, vertex_id: str, method: str) -> Optional[Dict[str, Any]]
# Compute or retrieve cached correlation matrix. Returns {col: {row: float}}.
compute_correlation: Callable[[str, str, str], Optional[Dict[str, Any]]] = lambda *_: None


# ---------------------------------------------------------------------------
# Schema editing
# ---------------------------------------------------------------------------

# (session_id: str) -> Optional[List[Dict[str, str]]]
# Return [{name, type}] for all columns in the root vertex schema.
# type is one of: numeric, categorical, ordered_categorical, service, excluded.
get_schema: Callable[[str], Optional[List[Dict[str, str]]]] = lambda _: None

# (session_id: str, schema_dict: Dict[str, str]) -> None
# Reassign column types in the root vertex schema based on {col_name: type} mapping.
update_schema: Callable[[str, Dict[str, str]], None] = lambda *_: None


# ---------------------------------------------------------------------------
# Transformation config editing
# ---------------------------------------------------------------------------

# (session_id: str, vertex_id: str, class_name: str, config: Dict[str, Any]) -> None
# Update the transformation config for an existing vertex and reset its state to 'initialized'.
update_transformation_config: Callable[[str, str, str, Dict[str, Any]], None] = lambda *_: None
