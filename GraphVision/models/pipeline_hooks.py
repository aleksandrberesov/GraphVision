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
] = lambda _s, nodes: nodes


# ---------------------------------------------------------------------------
# Data attachment
# ---------------------------------------------------------------------------

# (session_id: str, file_path: str, ext: str) -> Optional[Tuple[str, str]]
# Load a data file (csv/parquet), infer schema, attach to pipeline.
# Returns (root_vertex_id, file_stem) on success, None on failure or if
# no implementation is registered.
attach_data: Callable[
    [str, str, str], Optional[Tuple[str, str]]
] = lambda _s, _p, _e: None


# ---------------------------------------------------------------------------
# Pipeline operations
# ---------------------------------------------------------------------------

# (session_id: str, node_id: str) -> bool
# Fit and apply the transformation at node_id.  Returns True on success.
manifest_vertex: Callable[[str, str], bool] = lambda _s, _n: False

# (session_id: str, parent_id: str, class_name: str, config: Dict, ui_node_id: str) -> Optional[str]
# Add a transformation to the pipeline.  Returns the vertex_id used (may equal
# ui_node_id if the backend preserved it), or None on failure.
add_transformation: Callable[
    [str, str, str, Dict[str, Any], str], Optional[str]
] = lambda *_: None

# (session_id: str, path: str) -> None
save_yaml: Callable[[str, str], None] = lambda _s, _p: None

# (session_id: str, path: str) -> Optional[Tuple[List[Dict], List[Dict]]]
# Load a pipeline from YAML, register it, return (nodes, edges).
load_yaml: Callable[
    [str, str], Optional[Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]
] = lambda _s, _p: None
