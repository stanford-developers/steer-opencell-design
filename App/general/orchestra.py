from dash import html, dcc, callback, Output, Input, State
from dash.exceptions import PreventUpdate
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from typing import Dict
import time

from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.current_collectors.configs import COLLECTOR_CONFIGS, CollectorType


current_collector_trigger_stores = html.Div([
        dcc.Store(id={"type": "trigger", "callback": "update_cathode_punched_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_cathode_notched_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_cathode_tabless_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_cathode_tabbed_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_anode_punched_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_anode_notched_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_anode_tabless_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_anode_tabbed_current_collector"}, data=[]),
])


@dataclass
class TriggerCondition:
    """Configuration for a single trigger condition."""
    name: str
    check_function: Callable[[Any, Any], bool]
    description: str = ""


@dataclass
class CallbackTriggerConfig:
    """Configuration for when a callback should be triggered."""
    callback_name: str
    conditions: List[TriggerCondition]
    description: str = ""






@callback(
        [
            Output({"type": "trigger", "callback": "update_cathode_punched_current_collector"}, "data"),
            Output({"type": "trigger", "callback": "update_cathode_notched_current_collector"}, "data"),
            Output({"type": "trigger", "callback": "update_cathode_tabless_current_collector"}, "data"),
            Output({"type": "trigger", "callback": "update_cathode_tabbed_current_collector"}, "data"),
            Output({"type": "trigger", "callback": "update_anode_punched_current_collector"}, "data"),
            Output({"type": "trigger", "callback": "update_anode_notched_current_collector"}, "data"),
            Output({"type": "trigger", "callback": "update_anode_tabless_current_collector"}, "data"),
            Output({"type": "trigger", "callback": "update_anode_tabbed_current_collector"}, "data"),
        ],
        [
            Input("cell_store", "data"),
        ],
        [
            State("old_cell_store", "data"),
        ],
        prevent_initial_call=True,
)
def orchestrate_current_collector_callbacks(
    cell_data: Dict,
    old_cell_data: Dict,
    ):
    """
    Orchestrate all current collector callbacks by updating their trigger stores
    whenever the cell store is updated.
    """
    print("Orchestrating callbacks...")

    # Get the current timestamp
    time_stamp = time.time()

    # Get the cell keys
    cell_key = cell_data["cache_key"]
    old_cell_key = old_cell_data["cache_key"]

    # create default response
    response = [time_stamp] * 8

    # try to get the old cell from the state. If fails, then trigger all callbacks
    try:
        old_cell = get_cell_from_cache(old_cell_key)
    except Exception as e:
        return response

    # get the new cell from the store
    cell = get_cell_from_cache(cell_key)

    # get the current collector from the new cell
    cathode_current_collector = get_object_from_cell(cell, COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC])

    raise PreventUpdate


