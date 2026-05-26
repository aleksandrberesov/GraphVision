from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx

# Role options shown in the constructor dropdown, in display order.
_ROLES = [
    "none",
    "target",
    "exposure",
    "index",
    "force_drop",
    "force_numeric",
    "force_datetime",
    "force_categorical",
]


class BaseSchemaState(rx.State):
    """State for the base-schema constructor dialog.

    The constructor lets the user assign each dataset column a *role*
    (target pool, exposure pool, index, force-drop, force type-coercions, or
    plain feature) before the schema is built via DataSchema.from_dataframe.

    Design note — why column_role_items is a base state var, not computed
    -----------------------------------------------------------------------
    Reflex compiles local Vars from rx.foreach into JavaScript event-payload
    expressions.  This only works reliably when rx.foreach iterates over a
    *base* state var.  If the var is *computed* (derived from other vars),
    Reflex cannot produce the correct JS serialisation for local-Var partial
    event arguments (e.g. ``set_role(item["col"])``), so the server receives
    null/wrong column names, raises a Pydantic validation error, and the
    WebSocket resets — visible to the user as a "page reload" with all selects
    snapping back to "none".

    This is the same pattern used by ConfigState.param_schema → update_param,
    which iterates over a base List[Dict] state var and updates it in-place.
    """

    constructor_open: bool = False
    # Primary source of truth for the dialog: one dict per column.
    # Each item: {"col": column_name, "role": role_string}
    # This is a BASE state var (not computed) so that rx.foreach local-Var
    # partial event args serialise correctly.
    column_role_items: List[Dict[str, str]] = []

    @rx.event
    def set_constructor_open(self, value: bool):
        self.constructor_open = value

    @rx.event
    def set_role(self, col: str, role: str):
        """Update the role for *col* in place — mirrors ConfigState.update_param.

        Kept for backward compatibility.  Prefer set_role_by_index which avoids
        the JS closure-variable lookup that can silently send col=null.
        """
        self.column_role_items = [
            {**item, "role": role} if item["col"] == col else item
            for item in self.column_role_items
        ]

    @rx.event
    def set_role_by_index(self, idx: int, role: str):
        """Update the role at position *idx* in column_role_items.

        Uses the row index (from Array.prototype.map's second argument) instead
        of the column name so the event arg is a plain JS integer — never
        undefined / null — avoiding the bug where set_role(col=None) silently
        no-ops and the UI appears to reset all selections back to 'none'.

        Reassigns the whole list (same pattern as set_role) so MutableProxy
        marks the var dirty and a delta is emitted.
        """
        if idx < 0 or idx >= len(self.column_role_items):
            return
        self.column_role_items = [
            {**item, "role": role} if i == idx else item
            for i, item in enumerate(self.column_role_items)
        ]

    @rx.event
    async def open_constructor(self):
        """Load columns + prefill role assignments from the current schema."""
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        yield BusyState.show("Loading schema constructor…")
        info = pipeline_hooks.get_base_schema(session_id)
        yield BusyState.hide()
        if info is None:
            return

        all_columns: List[str] = info.get("all_columns", [])

        # Prefill roles from the existing schema
        roles: Dict[str, str] = {}
        for col in info.get("targets", []):
            roles[col] = "target"
        for col in info.get("exposures", []):
            roles[col] = "exposure"
        for col in info.get("indexes", []):
            roles[col] = "index"
        for col in info.get("force_drop", []):
            roles[col] = "force_drop"

        self.column_role_items = [
            {"col": col, "role": roles.get(col, "none")}
            for col in all_columns
        ]
        self.constructor_open = True

    @rx.event
    async def apply_constructor(self):
        """Build + persist the base schema from the current role assignments."""
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"

        base_dict: Dict[str, Any] = {
            "targets":           [i["col"] for i in self.column_role_items if i["role"] == "target"],
            "exposures":         [i["col"] for i in self.column_role_items if i["role"] == "exposure"],
            "indexes":           [i["col"] for i in self.column_role_items if i["role"] == "index"],
            "force_drop":        [i["col"] for i in self.column_role_items if i["role"] == "force_drop"],
            "force_numeric":     [i["col"] for i in self.column_role_items if i["role"] == "force_numeric"],
            "force_datetime":    [i["col"] for i in self.column_role_items if i["role"] == "force_datetime"],
            "force_categorical": [i["col"] for i in self.column_role_items if i["role"] == "force_categorical"],
        }

        yield BusyState.show("Applying base schema…")
        pipeline_hooks.build_base_schema(session_id, base_dict)

        # Inline the graph refresh in the same server-side batch.
        # Using get_state + direct assignment avoids the client round-trip
        # and explicitly keeps data_loaded = True so the control panel
        # never flashes the "No dataset loaded" empty-state.
        result = pipeline_hooks.pipeline_to_ui(session_id)
        if result is not None:
            graph_state.nodes, graph_state.edges = result
            graph_state.data_loaded = True

        yield BusyState.hide()
        self.constructor_open = False


class SchemaState(rx.State):
    is_open: bool = False
    rows: List[Dict[str, str]] = []

    @rx.event
    async def open_schema(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        if not pipeline_hooks.get_pipeline(session_id):
            return
        yield BusyState.show("Loading schema...")
        rows = pipeline_hooks.get_schema(session_id)
        yield BusyState.hide()
        if rows is not None:
            self.rows = rows
            self.is_open = True

    @rx.event
    def set_is_open(self, value: bool):
        self.is_open = value

    @rx.event
    def update_row_type(self, name: str, col_type: str):
        self.rows = [
            {**r, "type": col_type} if r["name"] == name else r
            for r in self.rows
        ]

    @rx.event
    async def save_schema(self):
        from .auth_state import AuthState
        from . import pipeline_hooks
        from .busy_state import BusyState
        from .graph import GraphState

        graph_state = await self.get_state(GraphState)
        session_id = f"{(await self.get_state(AuthState)).user_id}::{graph_state.project_name}"
        yield BusyState.show("Saving schema...")
        schema_dict = {r["name"]: r["type"] for r in self.rows}
        pipeline_hooks.update_schema(session_id, schema_dict)
        yield BusyState.hide()
        self.is_open = False
