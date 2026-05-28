"""
State for the GLM model node configuration dialog.

The user picks a GLM family and a link function (link list updates when
family changes), then clicks "Add model" to create a model vertex as a
child of the currently selected node.
"""

from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx


class ModelConfigState(rx.State):
    """Dialog state for the GLM model node configurator."""

    is_open: bool = False
    parent_vertex_id: str = ""

    # Family / link data loaded from backend
    families_data: Dict[str, Any] = {}

    # Current selections
    selected_family: str = "Gaussian"
    selected_link: str = "Identity"

    # ------------------------------------------------------------------ #
    # Computed vars                                                        #
    # ------------------------------------------------------------------ #

    @rx.var
    def family_names(self) -> List[str]:
        return sorted(self.families_data.keys())

    @rx.var
    def available_links(self) -> List[str]:
        fam = self.families_data.get(self.selected_family, {})
        return list(fam.get("available_links", []))

    @rx.var
    def canonical_link(self) -> str:
        fam = self.families_data.get(self.selected_family, {})
        return str(fam.get("canonical_link", "Identity"))

    @rx.var
    def can_apply(self) -> bool:
        return bool(self.selected_family and self.selected_link)

    # ------------------------------------------------------------------ #
    # Events                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        """Load families from backend and open the dialog."""
        from . import pipeline_hooks
        from .busy_state import BusyState

        yield BusyState.show("Loading model options…")
        families = pipeline_hooks.describe_glm_families()
        yield BusyState.hide()

        if not families:
            from .logger_state import LoggerState
            yield LoggerState.add_log(
                "Cannot open model dialog — no GLM families available.", "warning"
            )
            return

        self.families_data = families
        self.parent_vertex_id = parent_vertex_id

        # Default to Gaussian / Identity
        if "Gaussian" in families:
            self.selected_family = "Gaussian"
            self.selected_link = families["Gaussian"].get("canonical_link", "Identity")
        else:
            first = sorted(families.keys())[0]
            self.selected_family = first
            self.selected_link = families[first].get("canonical_link", "Identity")

        self.is_open = True

    @rx.event
    def close(self):
        self.is_open = False

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    @rx.event
    def set_family(self, family: str):
        self.selected_family = family
        # Switch link to canonical for the new family
        fam_data = self.families_data.get(family, {})
        canonical = fam_data.get("canonical_link", "")
        avail = fam_data.get("available_links", [])
        self.selected_link = canonical if canonical in avail else (avail[0] if avail else "")

    @rx.event
    def set_link(self, link: str):
        self.selected_link = link

    @rx.event
    async def apply(self):
        """Create a GLM model node as a child of the parent vertex."""
        if not self.selected_family or not self.selected_link:
            return

        from . import pipeline_hooks
        from .auth_state import AuthState
        from .graph import GraphState
        from .logger_state import LoggerState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"

        # Ensure the correct parent is selected before GraphState.add_model_node
        if self.parent_vertex_id:
            yield graph_state._select_node(self.parent_vertex_id)

        self.is_open = False
        yield GraphState.add_model_node(
            self.parent_vertex_id,
            self.selected_family,
            self.selected_link,
        )
