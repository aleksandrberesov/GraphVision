"""
State for the Tiny Schema node configuration dialog.

Tiny Schema (Node 1 in the scenario) begins each graph branch by selecting:
  - ONE target from the root schema's target pool
  - ONE exposure from the root schema's exposure pool
  - ONE index from the root schema's index pool
  - A feature column list (kept and passed downstream)

Different branches can carry different Tiny Schemas, enabling multiple parallel
experiments from the same Node 0.
"""

from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx


class TinySchemaState(rx.State):
    """Dialog state for the Tiny Schema node configurator."""

    is_open: bool = False
    parent_vertex_id: str = ""

    # Pools loaded from the backend
    target_options: List[str] = []
    exposure_options: List[str] = []
    index_options: List[str] = []
    feature_options: List[str] = []

    # Current selections
    selected_target: str = ""
    selected_exposure: str = ""
    selected_index: str = ""
    selected_features: List[str] = []

    # "Create new" service columns for this branch: synthesise a constant-1
    # exposure / 0..N-1 index under the reserve name when the pool lacks one.
    create_exposure: bool = False
    create_index: bool = False
    reserve_exposure_name: str = "exposure"
    reserve_index_name: str = "index"

    # ------------------------------------------------------------------ #
    # Computed vars                                                        #
    # ------------------------------------------------------------------ #

    @rx.var
    def pure_feature_options(self) -> List[str]:
        """Feature options with the chosen target / exposure / index removed
        (they are always included and handled by their own dropdowns)."""
        service = {self.selected_target, self.selected_exposure, self.selected_index}
        return [f for f in self.feature_options if f not in service and f]

    @rx.var
    def can_apply(self) -> bool:
        has_exposure = bool(self.selected_exposure) or self.create_exposure
        has_index = bool(self.selected_index) or self.create_index
        return bool(self.selected_target) and has_exposure and has_index

    # ------------------------------------------------------------------ #
    # Events                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        """Load pools from backend and open the dialog."""
        from .auth_state import AuthState
        from .graph import GraphState
        from . import pipeline_hooks
        from .busy_state import BusyState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"

        yield BusyState.show("Loading Tiny Schema options…")
        pools = pipeline_hooks.get_tiny_schema_pools(session_id, parent_vertex_id)
        yield BusyState.hide()

        if pools is None:
            from .logger_state import LoggerState
            yield LoggerState.add_log(
                "Cannot open Tiny Schema — parent node is not manifested yet. "
                "Apply the parent node first.",
                "warning",
            )
            return

        self.parent_vertex_id = parent_vertex_id
        self.target_options  = pools.get("targets",   [])
        self.exposure_options = pools.get("exposures", [])
        self.index_options   = pools.get("indexes",   [])
        self.feature_options  = pools.get("features",  [])

        # Reserve names for "Create new"; reset the toggles for this open.
        self.reserve_exposure_name = pools.get("reserve_exposure_name", "exposure")
        self.reserve_index_name = pools.get("reserve_index_name", "index")
        self.create_exposure = False
        self.create_index = False

        # Defaults: first item for role selects; all features selected
        self.selected_target   = self.target_options[0]   if self.target_options   else ""
        self.selected_exposure = self.exposure_options[0] if self.exposure_options else ""
        self.selected_index    = self.index_options[0]    if self.index_options    else ""
        self.selected_features = list(self.feature_options)

        self.is_open = True

    @rx.event
    def close(self):
        self.is_open = False

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    @rx.event
    def set_target(self, value: str):
        self.selected_target = value

    @rx.event
    def set_exposure(self, value: str):
        # Picking a real exposure supersedes a pending "Create new".
        self.selected_exposure = value
        self.create_exposure = False

    @rx.event
    def set_index(self, value: str):
        self.selected_index = value
        self.create_index = False

    @rx.event
    def create_new_exposure(self):
        """Toggle creating a constant-1 exposure column for this branch."""
        self.create_exposure = not self.create_exposure
        if self.create_exposure:
            self.selected_exposure = self.reserve_exposure_name
        elif self.selected_exposure == self.reserve_exposure_name:
            self.selected_exposure = ""

    @rx.event
    def create_new_index(self):
        """Toggle creating a 0..N-1 range index column for this branch."""
        self.create_index = not self.create_index
        if self.create_index:
            self.selected_index = self.reserve_index_name
        elif self.selected_index == self.reserve_index_name:
            self.selected_index = ""

    @rx.event
    def toggle_feature(self, col: str):
        if col in self.selected_features:
            self.selected_features = [f for f in self.selected_features if f != col]
        else:
            self.selected_features = self.selected_features + [col]

    @rx.event
    def select_all_features(self):
        self.selected_features = list(self.feature_options)

    @rx.event
    def clear_all_features(self):
        self.selected_features = []

    @rx.event
    async def apply(self):
        """Build config dict and add a GLMTinySchemaTransformation node."""
        if not self.selected_target:
            return

        config: Dict[str, Any] = {
            "target":          self.selected_target,
            "exposure":        self.selected_exposure,
            "index":           self.selected_index,
            "feature_columns": list(self.selected_features),
            "create_exposure": self.create_exposure,
            "create_index":    self.create_index,
        }

        from .graph import GraphState
        graph_state = await self.get_state(GraphState)

        # Make sure the correct parent is selected before add_transformation_node
        # reads graph_state.selected_node_id.
        if self.parent_vertex_id:
            yield graph_state._select_node(self.parent_vertex_id)

        self.is_open = False
        yield GraphState.add_transformation_node("GLMTinySchemaTransformation", config)
