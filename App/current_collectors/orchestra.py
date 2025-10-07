from dash import html, dcc, callback, Input, State, set_props
from typing import Dict
from typing import Dict
import time

from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.current_collectors.layout_configs import COLLECTOR_CONFIGS, CollectorType
from App.materials.configs import MaterialType, MATERIAL_CONFIGS
from App.general.orchestra import is_visible, CallbackTriggerConfig, TriggerCondition, has_changed

from steer_opencell_design.Components.CurrentCollectors import (
    PunchedCurrentCollector,
    NotchedCurrentCollector,
    TablessCurrentCollector,
    TabWeldedCurrentCollector,
)

##############################
####### Trigger Stores #######
##############################


current_collector_trigger_stores = html.Div([

        dcc.Store(id={"type": "trigger", "callback": "update_cathode_current_collector_design"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_cathode_punched_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_cathode_notched_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_cathode_tabless_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_cathode_tabbed_current_collector"}, data=[]),

        dcc.Store(id={"type": "trigger", "callback": "update_cathode_current_collector_material"}, data=[]),

        dcc.Store(id={"type": "trigger", "callback": "update_anode_current_collector_design"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_anode_punched_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_anode_notched_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_anode_tabless_current_collector"}, data=[]),
        dcc.Store(id={"type": "trigger", "callback": "update_anode_tabbed_current_collector"}, data=[]),

        dcc.Store(id={"type": "trigger", "callback": "update_anode_current_collector_material"}, data=[]),

])

##############################
##### Trigger Conditions #####
##############################

def is_punched(new_cell, config: CollectorType) -> bool:
    """Check if cathode collector is punched type."""
    try:
        collector = get_object_from_cell(new_cell, config)
        return isinstance(collector, PunchedCurrentCollector)
    except Exception as e:
        return False

def is_notched(new_cell, config: CollectorType) -> bool:
    """Check if cathode collector is notched type."""
    try:
        collector = get_object_from_cell(new_cell, config)
        return isinstance(collector, NotchedCurrentCollector)
    except Exception as e:
        return False

def is_tabless(new_cell, config: CollectorType) -> bool:
    """Check if cathode collector is tabless type."""
    try:
        collector = get_object_from_cell(new_cell, config)
        return isinstance(collector, TablessCurrentCollector)
    except Exception as e:
        return False

def is_tabbed(new_cell, config: CollectorType) -> bool:
    """Check if cathode collector is tabbed type."""
    try:
        collector = get_object_from_cell(new_cell, config)
        return isinstance(collector, TabWeldedCurrentCollector)
    except Exception as e:
        return False


##############################
##### Trigger Configs ########
##############################


COLLECTOR_TRIGGER_CONFIGS = {

    "update_cathode_current_collector_design": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab", 
            "tabs_panel"
        ]
    ),
    "update_cathode_punched_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_PUNCHED],
        conditions=[TriggerCondition(check_function=is_punched)],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab", 
            "tabs_panel"
        ]
    ),
    "update_cathode_notched_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_NOTCHED],
        conditions=[TriggerCondition(check_function=is_notched)],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),
    "update_cathode_tabless_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_TABLESS],
        conditions=[TriggerCondition(check_function=is_tabless)],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),
    "update_cathode_tabbed_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_TABBED],
        conditions=[TriggerCondition(check_function=is_tabbed)],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),

    "update_anode_current_collector_design": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC],
        required_visibility=[
            "anode_tab", 
            "tabs_panel"
        ]
    ),
    "update_anode_punched_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_PUNCHED],
        conditions=[TriggerCondition(check_function=is_punched)],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_notched_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_NOTCHED],
        conditions=[TriggerCondition(check_function=is_notched)],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_tabless_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_TABLESS],
        conditions=[TriggerCondition(check_function=is_tabless)],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_tabbed_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_TABBED],
        conditions=[TriggerCondition(check_function=is_tabbed)],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),

    "update_cathode_current_collector_material": CallbackTriggerConfig(
        config=MATERIAL_CONFIGS[MaterialType.CATHODE_CURRENT_COLLECTOR],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_current_collector_material": CallbackTriggerConfig(
        config=MATERIAL_CONFIGS[MaterialType.ANODE_CURRENT_COLLECTOR],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),

}


##############################
##### Callback Triggers #####
##############################


@callback(
        [
            # cell inputs
            Input("cell_store", "data"),
            Input("old_cell_store", "data"),

            # cathode visibility states
            Input("cathode_current_collector_tab", "style"),
            Input("cathode_tab", "style"),

            # anode visibility states
            Input("anode_current_collector_tab", "style"),
            Input("anode_tab", "style"),

            # global visibility states
            Input("tabs_panel", "style"),
        ],
        [
            State("last_triggered", "data"),
        ],
        prevent_initial_call=True,
)
def orchestrate_current_collector_callbacks(
    cell_data: Dict,
    old_cell_data: Dict,
    cathode_cc_tab_style: Dict,
    cathode_tab_style: Dict,
    anode_cc_tab_style: Dict,
    anode_tab_style: Dict,
    tabs_panel_style: Dict,
    last_triggered_callback: str,
    ):
    """
    Orchestrate all current collector callbacks by updating their trigger stores
    whenever the cell store is updated.
    """
    print("Orchestrating current collector callbacks...")

    # Get the current timestamp
    time_stamp = time.time()

    # Define callback order to match outputs
    callbacks = list(COLLECTOR_TRIGGER_CONFIGS.keys())

    # Create visibility context
    visibility_styles = {
        "cathode_current_collector_tab": cathode_cc_tab_style,
        "cathode_tab": cathode_tab_style,
        "anode_current_collector_tab": anode_cc_tab_style,
        "anode_tab": anode_tab_style,
        "tabs_panel": tabs_panel_style,
    }

    # Get the cell keys
    cell_key = cell_data["cache_key"]

    # get the current cell from cache
    new_cell = get_cell_from_cache(cell_key)

    # get the old cell from cache
    try:
        old_cell_key = old_cell_data["cache_key"]
        old_cell = get_cell_from_cache(old_cell_key)
    except Exception as e:
        old_cell = None
        print("No old cell found in cache.")

    # Evaluate each callback's trigger conditions
    for callback_name in callbacks:

        # Get the trigger config
        trigger_config = COLLECTOR_TRIGGER_CONFIGS.get(callback_name)
        
        # Create dictionary of boolean conditions that must all be true
        conditions_dict = {}
        
        # Condition 1: Visibility check
        required_visibility_condition = trigger_config.required_visibility
        required_styles = [visibility_styles.get(element_id) for element_id in required_visibility_condition]
        visibility_condition = is_visible(required_styles)
        conditions_dict["visibility"] = visibility_condition
        
        # Condition 2: Anti-circular logic
        circular_condition = last_triggered_callback != callback_name
        conditions_dict["anti_circular"] = circular_condition

        # Condition 3: Object change check
        if old_cell is not None:
            object_changed_condition = has_changed(old_cell, new_cell, trigger_config.config)
        else:
            object_changed_condition = True  # If no old cell, assume changed
        conditions_dict["object_changed"] = object_changed_condition

        # Condition 4: Callback-specific conditions (if any)
        if trigger_config.conditions:
            for condition in trigger_config.conditions:
                condition_result = condition.check_function(new_cell, trigger_config.config)
                condition_name = getattr(condition, 'name', condition.check_function.__name__)
                conditions_dict[condition_name] = condition_result
        
        print(f"callback name: {callback_name}, conditions: {conditions_dict}")

        # Trigger only if ALL conditions are True
        if all(conditions_dict.values()):
            print(f"############ Triggering {callback_name}... ################")
            set_props({"type": "trigger", "callback": callback_name}, {"data": time_stamp})

