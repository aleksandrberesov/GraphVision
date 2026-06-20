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

    # Step 1 — column selection (which features go to the model) + stability
    available_columns: List[str] = []
    selected_columns: List[str] = []          # the columns kept; unselected are dropped
    stability_text: str = "—"

    # Step 3 — GLM formula preview (built server-side before fitting)
    formula_text: str = ""
    formula_warning: str = ""

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
        return bool(
            self.selected_family and self.selected_link and self.selected_columns
        )

    @rx.var
    def removed_preview(self) -> List[str]:
        """Feature columns that will be dropped (everything not kept)."""
        return [c for c in self.available_columns if c not in self.selected_columns]

    # ------------------------------------------------------------------ #
    # Events                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str):
        """Load families + parent columns from backend and open the dialog."""
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .busy_state import BusyState
        from .graph import GraphState

        yield BusyState.show("Loading model options…")
        families = pipeline_hooks.describe_glm_families()

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"
        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_vertex_id)
        yield BusyState.hide()

        if not families:
            from .logger_state import LoggerState
            yield LoggerState.add_log(
                "Cannot open model dialog — no GLM families available.", "warning"
            )
            return

        self.families_data = families
        self.parent_vertex_id = parent_vertex_id

        # Feature columns the user can route to the model (service columns —
        # target / exposure / index — are kept automatically and not listed).
        cols: List[str] = []
        if cols_by_type:
            for key in ("numeric", "categorical", "ordered_categorical"):
                cols.extend(cols_by_type.get(key, []))
        self.available_columns = cols
        self.selected_columns = list(cols)   # start with everything kept
        self.stability_text = "—"
        self.formula_text = ""
        self.formula_warning = ""

        # Default to Gaussian / Identity
        if "Gaussian" in families:
            self.selected_family = "Gaussian"
            self.selected_link = families["Gaussian"].get("canonical_link", "Identity")
        else:
            first = sorted(families.keys())[0]
            self.selected_family = first
            self.selected_link = families[first].get("canonical_link", "Identity")

        self.is_open = True

    # ------------------------------------------------------------------ #
    # Step 1 — column selection + stability                                #
    # ------------------------------------------------------------------ #

    @rx.event
    def toggle_column(self, col: str):
        if col in self.selected_columns:
            self.selected_columns = [c for c in self.selected_columns if c != col]
        else:
            self.selected_columns = self.selected_columns + [col]
        self.stability_text = "—"   # selection changed — stale until recomputed
        self.formula_text = ""

    @rx.event
    def select_all_columns(self):
        self.selected_columns = list(self.available_columns)
        self.stability_text = "—"
        self.formula_text = ""

    @rx.event
    def clear_columns(self):
        self.selected_columns = []
        self.stability_text = "—"
        self.formula_text = ""

    @rx.event
    async def recompute_stability(self):
        """Multicollinearity readout for the kept columns."""
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .graph import GraphState

        if not self.parent_vertex_id:
            return
        graph_state = await self.get_state(GraphState)
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        result = pipeline_hooks.compute_columns_stability(
            session_id, self.parent_vertex_id, self.selected_columns
        )
        if not result:
            self.stability_text = "—"
            return
        n = int(result.get("n_numeric", 0))
        if n < 2:
            self.stability_text = f"{n} numeric column(s) — need ≥2 for stability."
            return
        parts: List[str] = []
        cond = result.get("condition_number")
        if cond is not None:
            parts.append(f"cond={float(cond):.3g}")
        rank = result.get("rank")
        exp = result.get("expected_rank")
        if rank is not None and exp is not None:
            parts.append(f"rank={int(rank)}/{int(exp)}")
        vif = result.get("vif_max")
        if vif is not None:
            parts.append(f"VIF max={float(vif):.3g}")
        self.stability_text = "  ·  ".join(parts) if parts else "—"

    # ------------------------------------------------------------------ #
    # Step 3 — formula preview                                             #
    # ------------------------------------------------------------------ #

    @rx.event
    async def preview_formula(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .graph import GraphState

        if not self.parent_vertex_id:
            return
        graph_state = await self.get_state(GraphState)
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        result = pipeline_hooks.describe_model_formula(
            session_id, self.parent_vertex_id, self.selected_columns,
            self.selected_family, self.selected_link,
        )
        if result:
            self.formula_text = result.get("formula", "")
            self.formula_warning = result.get("warning", "")
        else:
            self.formula_text = ""
            self.formula_warning = "Could not build the formula preview."

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
        self.formula_text = ""   # family/link changed — preview is stale

    @rx.event
    def set_link(self, link: str):
        self.selected_link = link
        self.formula_text = ""

    @rx.event
    async def apply(self):
        """Option A: auto-insert ColumnRemover → hidden Transliterator → model
        upstream of the parent, dropping unselected columns, then select the model."""
        if not (self.selected_family and self.selected_link and self.selected_columns):
            return

        from .graph import GraphState
        graph_state = await self.get_state(GraphState)

        self.is_open = False
        yield GraphState.add_model_flow(
            self.parent_vertex_id,
            list(self.selected_columns),
            self.selected_family,
            self.selected_link,
        )
