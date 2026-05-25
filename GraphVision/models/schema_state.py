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
    """

    constructor_open: bool = False
    all_columns: List[str] = []
    # col_name → role string (one of _ROLES above; "none" means auto-type)
    column_roles: Dict[str, str] = {}

    @rx.var
    def column_roles_list(self) -> List[List[str]]:
        """Computed list of [col, role] pairs for rx.foreach rendering."""
        return [[col, self.column_roles.get(col, "none")] for col in self.all_columns]

    @rx.event
    def set_constructor_open(self, value: bool):
        self.constructor_open = value

    @rx.event
    def set_role(self, col: str, role: str):
        self.column_roles = {**self.column_roles, col: role}

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

        self.all_columns = info.get("all_columns", [])

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
        self.column_roles = roles
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
            "targets":           [c for c, r in self.column_roles.items() if r == "target"],
            "exposures":         [c for c, r in self.column_roles.items() if r == "exposure"],
            "indexes":           [c for c, r in self.column_roles.items() if r == "index"],
            "force_drop":        [c for c, r in self.column_roles.items() if r == "force_drop"],
            "force_numeric":     [c for c, r in self.column_roles.items() if r == "force_numeric"],
            "force_datetime":    [c for c, r in self.column_roles.items() if r == "force_datetime"],
            "force_categorical": [c for c, r in self.column_roles.items() if r == "force_categorical"],
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
