from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx

# Role options in display order (drives section order in the constructor panel).
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

# Tier-1 roles are mutually exclusive: a column can hold at most one of these.
# Exposure additionally requires the column to be numeric and allows only one
# column to hold it at a time.
_TIER1_ROLES: set = {"none", "target", "index", "exposure"}

# Tier-2 flags are independent boolean overrides: any column can carry any
# combination of these regardless of its tier-1 role.
_TIER2_FLAGS: set = {"force_drop", "force_numeric", "force_datetime", "force_categorical"}


class BaseSchemaState(rx.State):
    """State for the base-schema constructor dialog.

    Two-tier role model (mirrors the notebook MultiTabSelector):
      Tier-1 (exclusive): none / target / index / exposure
        - A column holds exactly one tier-1 role.
        - Exposure additionally requires is_numeric=True and allows only one
          column at a time.
      Tier-2 (independent flags): force_drop / force_numeric / force_datetime / force_categorical
        - Each flag is a boolean independent of the tier-1 role and of each
          other, so a column can be "target" AND "force_categorical" at once.

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
    # "Create new" service columns: when set, a synthetic exposure (constant 1)
    # / index (0..N-1 range) is created on apply under the reserve name.
    create_exposure: bool = False
    create_index: bool = False
    reserve_exposure_name: str = "exposure"
    reserve_index_name: str = "index"
    # Primary source of truth for the dialog: one dict per column.
    # Each item: {
    #   "col":              str,
    #   "role":             str,   # tier-1: "none" | "target" | "index" | "exposure"
    #   "force_drop":       bool,  # tier-2 flags (independent)
    #   "force_numeric":    bool,
    #   "force_datetime":   bool,
    #   "force_categorical": bool,
    #   "is_numeric":       bool,  # True when the DataFrame column is numeric
    #   "val0":             str,
    #   "val1":             str,
    # }
    # BASE var (not computed) so rx.foreach local-Var event args serialise correctly.
    column_role_items: List[Dict[str, Any]] = []

    @rx.var
    def can_apply(self) -> bool:
        """True only when at least one target and one index column are assigned.

        A "Create new" index satisfies the index requirement.
        """
        has_target = any(item["role"] == "target" for item in self.column_role_items)
        has_index = any(item["role"] == "index" for item in self.column_role_items) or self.create_index
        return has_target and has_index

    @rx.var
    def has_exposure_assigned(self) -> bool:
        return any(item["role"] == "exposure" for item in self.column_role_items)

    @rx.event
    def set_constructor_open(self, value: bool):
        self.constructor_open = value

    @rx.event
    def create_new_exposure(self):
        """Toggle creation of a synthetic constant-1 exposure column."""
        self.create_exposure = not self.create_exposure

    @rx.event
    def create_new_index(self):
        """Toggle creation of a synthetic 0..N-1 range index column."""
        self.create_index = not self.create_index

    @rx.event
    def toggle_tier1_by_index(self, idx: int, role: str):
        """Toggle a tier-1 role (none / target / index / exposure) for the column at *idx*.

        Tier-1 roles are mutually exclusive: clicking assigns the column to
        *role*; clicking again (same role) reverts it to "none".  Exposure has
        two extra constraints enforced server-side:
          - the column must be numeric (is_numeric guard);
          - at most one column may hold "exposure" at a time (the previous
            exposure is automatically cleared when a new one is assigned).
        """
        if idx < 0 or idx >= len(self.column_role_items):
            return
        item = self.column_role_items[idx]
        if role == "exposure" and not item.get("is_numeric", False):
            return
        current = item["role"]
        new_role = "none" if current == role else role
        # A real exposure assignment supersedes a pending "Create new" exposure
        # (exposure is single).
        if new_role == "exposure":
            self.create_exposure = False
        new_items = []
        for i, it in enumerate(self.column_role_items):
            if i == idx:
                new_items.append({**it, "role": new_role})
            elif new_role == "exposure" and it["role"] == "exposure":
                new_items.append({**it, "role": "none"})
            else:
                new_items.append(it)
        self.column_role_items = new_items

    @rx.event
    def toggle_tier2_by_index(self, idx: int, flag: str):
        """Toggle an independent tier-2 force flag for the column at *idx*.

        The flag is flipped regardless of the column's tier-1 role, so a
        column can simultaneously be "target" and have "force_categorical" set.
        """
        if idx < 0 or idx >= len(self.column_role_items):
            return
        if flag not in _TIER2_FLAGS:
            return
        self.column_role_items = [
            {**item, flag: not item.get(flag, False)} if i == idx else item
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
        numeric_cols: set = set(info.get("numeric_columns", []))

        # Reserve names for "Create new" service columns; reset the toggles.
        self.reserve_exposure_name = info.get("reserve_exposure_name", "exposure")
        self.reserve_index_name = info.get("reserve_index_name", "index")
        self.create_exposure = False
        self.create_index = False

        # Prefill tier-1 roles from the existing schema.
        roles: Dict[str, str] = {}
        for col in info.get("targets", []):
            roles[col] = "target"
        for col in info.get("exposures", []):
            roles[col] = "exposure"
        for col in info.get("indexes", []):
            roles[col] = "index"

        # Prefill tier-2 flags.
        force_drop_set:        set = set(info.get("force_drop", []))
        force_numeric_set:     set = set(info.get("force_numeric", []))
        force_datetime_set:    set = set(info.get("force_datetime", []))
        force_categorical_set: set = set(info.get("force_categorical", []))

        samples: Dict[str, list] = info.get("column_samples", {})
        self.column_role_items = [
            {
                "col":               col,
                "role":              roles.get(col, "none"),
                "force_drop":        col in force_drop_set,
                "force_numeric":     col in force_numeric_set,
                "force_datetime":    col in force_datetime_set,
                "force_categorical": col in force_categorical_set,
                "is_numeric":        col in numeric_cols,
                "val0":              samples.get(col, ["—", "—"])[0],
                "val1":              samples.get(col, ["—", "—"])[1],
            }
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

        exposures = [i["col"] for i in self.column_role_items if i["role"] == "exposure"]
        indexes = [i["col"] for i in self.column_role_items if i["role"] == "index"]
        # "Create new" — append the reserve name so the backend materialises it
        # (constant 1.0 exposure / 0..N-1 index). Skip exposure if a real one exists.
        if self.create_exposure and not exposures and self.reserve_exposure_name not in exposures:
            exposures.append(self.reserve_exposure_name)
        if self.create_index and self.reserve_index_name not in indexes:
            indexes.append(self.reserve_index_name)

        base_dict: Dict[str, Any] = {
            "targets":           [i["col"] for i in self.column_role_items if i["role"] == "target"],
            "exposures":         exposures,
            "indexes":           indexes,
            "force_drop":        [i["col"] for i in self.column_role_items if i.get("force_drop", False)],
            "force_numeric":     [i["col"] for i in self.column_role_items if i.get("force_numeric", False)],
            "force_datetime":    [i["col"] for i in self.column_role_items if i.get("force_datetime", False)],
            "force_categorical": [i["col"] for i in self.column_role_items if i.get("force_categorical", False)],
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
