"""
Shared state for simple "pick columns" transformer dialogs.

Two transformers reduce to a single multi-select of columns, so they share
one builder, parameterised by ``target_class`` / ``mode``:

* **GLMDateTransformation** (mode ``"keep"``) — the selected columns are the
  ``date_columns`` list directly.
* **GLMColumnRemoverTransformation** (mode ``"remove_complement"``) — the user
  picks the columns to **keep**; on submit the complement (everything not kept)
  becomes ``columns_to_remove``. Starts with all columns selected.

Off-spec constructor params (date_format, keep_original, collision_strategy)
are filled with sensible defaults here and never shown.
"""

from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx


class ColumnPickerState(rx.State):
    """Dialog state for the shared single-multiselect column pickers."""

    is_open: bool = False
    is_edit_mode: bool = False
    vertex_id_editing: str = ""
    parent_vertex_id: str = ""

    # What we're building
    target_class: str = ""
    mode: str = "keep"  # "keep" | "remove_complement"
    title: str = ""
    icon: str = "columns"
    hint: str = ""

    available_columns: List[str] = []
    selected_columns: List[str] = []

    # ------------------------------------------------------------------ #
    # Computed                                                             #
    # ------------------------------------------------------------------ #

    @rx.var
    def can_submit(self) -> bool:
        # Always keep at least one column (Date needs ≥1 date col; ColumnRemover
        # must not drop the entire dataset).
        return bool(self.selected_columns)

    @rx.var
    def removed_preview(self) -> List[str]:
        """For ColumnRemover: the columns that will be dropped (the complement)."""
        if self.mode != "remove_complement":
            return []
        return [c for c in self.available_columns if c not in self.selected_columns]

    # ------------------------------------------------------------------ #
    # Open / close                                                         #
    # ------------------------------------------------------------------ #

    async def _load_all_columns(self, parent_vertex_id: str) -> List[str]:
        from . import pipeline_hooks
        from .auth_state import AuthState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        user_id = (await self.get_state(AuthState)).user_id
        session_id = f"{user_id}::{graph_state.project_name}"
        cols_by_type = pipeline_hooks.get_vertex_columns(session_id, parent_vertex_id)
        cols: List[str] = []
        if cols_by_type:
            for col_list in cols_by_type.values():
                cols.extend(col_list)
        return cols

    def _configure(self, target_class: str):
        """Set the per-transformer presentation/behaviour."""
        self.target_class = target_class
        if target_class == "GLMDateTransformation":
            self.mode = "keep"
            self.title = "Date columns"
            self.icon = "calendar"
            self.hint = "Select the date columns to convert."
        elif target_class == "GLMColumnRemoverTransformation":
            self.mode = "remove_complement"
            self.title = "Columns to keep"
            self.icon = "trash-2"
            self.hint = "Select the columns that go to the model. Unselected columns are removed."
        else:
            self.mode = "keep"
            self.title = "Select columns"
            self.icon = "columns"
            self.hint = ""

    @rx.event
    async def open_for_parent(self, parent_vertex_id: str, target_class: str):
        """Open in add-mode for the given parent vertex and transformer class."""
        from .busy_state import BusyState

        yield BusyState.show("Loading columns…")
        cols = await self._load_all_columns(parent_vertex_id)
        yield BusyState.hide()

        self._configure(target_class)
        self.parent_vertex_id = parent_vertex_id
        self.available_columns = cols
        # ColumnRemover starts with everything kept; Date starts empty.
        self.selected_columns = list(cols) if self.mode == "remove_complement" else []
        self.is_edit_mode = False
        self.vertex_id_editing = ""
        self.is_open = True

    @rx.event
    async def open_edit_dialog(
        self, vertex_id: str, target_class: str, existing_config: Dict[str, Any]
    ):
        """Open in edit-mode pre-filled from existing config."""
        from .busy_state import BusyState
        from .graph import GraphState

        yield BusyState.show("Loading columns…")
        graph_state = await self.get_state(GraphState)
        parent_id = next(
            (e["source"] for e in graph_state.edges if e["target"] == vertex_id),
            None,
        ) or vertex_id
        cols = await self._load_all_columns(parent_id)
        yield BusyState.hide()

        self._configure(target_class)
        self.parent_vertex_id = parent_id
        self.available_columns = cols

        if self.mode == "remove_complement":
            removed = existing_config.get("columns_to_remove", []) or []
            self.selected_columns = [c for c in cols if c not in removed]
        else:
            self.selected_columns = list(existing_config.get("date_columns", []) or [])

        self.is_edit_mode = True
        self.vertex_id_editing = vertex_id
        self.is_open = True

    @rx.event
    def close(self):
        self.is_open = False

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    # ------------------------------------------------------------------ #
    # Selection                                                            #
    # ------------------------------------------------------------------ #

    @rx.event
    def toggle_column(self, col: str):
        if col in self.selected_columns:
            self.selected_columns = [c for c in self.selected_columns if c != col]
        else:
            self.selected_columns = self.selected_columns + [col]

    @rx.event
    def select_all(self):
        self.selected_columns = list(self.available_columns)

    @rx.event
    def clear_all(self):
        self.selected_columns = []

    # ------------------------------------------------------------------ #
    # Submit                                                               #
    # ------------------------------------------------------------------ #

    @rx.event
    async def submit(self):
        if not self.selected_columns:
            yield rx.toast.error("Select at least one column.")
            return

        if self.mode == "remove_complement":
            columns_to_remove = [
                c for c in self.available_columns if c not in self.selected_columns
            ]
            config: Dict[str, Any] = {"columns_to_remove": columns_to_remove}
        else:
            config = {
                "date_columns": list(self.selected_columns),
                "keep_original": True,
            }

        from .graph import GraphState
        graph_state = await self.get_state(GraphState)
        self.is_open = False

        if self.is_edit_mode:
            from .auth_state import AuthState
            from . import pipeline_hooks
            session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
            pipeline_hooks.update_transformation_config(
                session_id,
                self.vertex_id_editing,
                self.target_class,
                config,
            )
            self.is_edit_mode = False
            self.vertex_id_editing = ""
            yield GraphState.refresh_statuses_from_pipeline()
        else:
            if self.parent_vertex_id:
                yield graph_state._select_node(self.parent_vertex_id)
            yield GraphState.add_transformation_node(self.target_class, config)
