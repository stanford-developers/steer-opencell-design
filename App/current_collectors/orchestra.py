from dash import html, dcc, callback, Input, State, set_props
from typing import Dict, Optional, List
import time

from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.current_collectors.layout_configs import COLLECTOR_CONFIGS, CollectorType
from App.materials.configs import MaterialType, MATERIAL_CONFIGS
from App.general.orchestra import is_visible, has_changed, has_type_changed, CallbackTriggerConfig, TriggerCondition

from steer_opencell_design.Components.CurrentCollectors import (
    PunchedCurrentCollector,
    NotchedCurrentCollector,
    TablessCurrentCollector,
    TabWeldedCurrentCollector,
)

##############################
####### Trigger Stores #######
##############################

def create_trigger_store(callback_name: str) -> dcc.Store:
    """Create a trigger store for a callback."""
    return dcc.Store(id={"type": "trigger", "callback": callback_name}, data=[])

CATHODE_CALLBACKS = [
    "update_cathode_current_collector_design",
    "update_cathode_punched_current_collector",
    "update_cathode_notched_current_collector",
    "update_cathode_tabless_current_collector",
    "update_cathode_tabbed_current_collector",
    "update_cathode_current_collector_material",
]

ANODE_CALLBACKS = [
    "update_anode_current_collector_design",
    "update_anode_punched_current_collector",
    "update_anode_notched_current_collector",
    "update_anode_tabless_current_collector",
    "update_anode_tabbed_current_collector",
    "update_anode_current_collector_material",
]

ALL_CALLBACKS = CATHODE_CALLBACKS + ANODE_CALLBACKS

# create the stores
current_collector_trigger_stores = html.Div([
    create_trigger_store(callback_name) for callback_name in ALL_CALLBACKS
])

##############################
##### Trigger Conditions #####
##############################

def is_punched(old_cell, new_cell, config: CollectorType) -> bool:
    collector = get_object_from_cell(new_cell, config)
    return isinstance(collector, PunchedCurrentCollector)

def is_notched(old_cell, new_cell, config: CollectorType) -> bool:
    """Check if collector is notched type."""
    collector = get_object_from_cell(new_cell, config)
    return isinstance(collector, NotchedCurrentCollector)

def is_tabless(old_cell, new_cell, config: CollectorType) -> bool:
    """Check if collector is tabless type."""
    collector = get_object_from_cell(new_cell, config)
    return isinstance(collector, TablessCurrentCollector)

def is_tabbed(old_cell, new_cell, config: CollectorType) -> bool:
    """Check if collector is tabbed type."""
    collector = get_object_from_cell(new_cell, config)
    return isinstance(collector, TabWeldedCurrentCollector)

##############################
##### Trigger Configs ########
##############################

COLLECTOR_TRIGGER_CONFIGS = {

    "update_cathode_current_collector_design": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC],
        conditions=[
            TriggerCondition(check_function=has_type_changed)
        ],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab", 
            "tabs_panel"
        ]
    ),
    "update_cathode_punched_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_PUNCHED],
        conditions=[
            TriggerCondition(check_function=has_changed),
            TriggerCondition(check_function=is_punched),
        ],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab", 
            "tabs_panel"
        ]
    ),
    "update_cathode_notched_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_NOTCHED],
        conditions=[
            TriggerCondition(check_function=has_changed),
            TriggerCondition(check_function=is_notched),
        ],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),
    "update_cathode_tabless_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_TABLESS],
        conditions=[
            TriggerCondition(check_function=has_changed),
            TriggerCondition(check_function=is_tabless),
        ],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),
    "update_cathode_tabbed_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_TABBED],
        conditions=[
            TriggerCondition(check_function=has_changed),
            TriggerCondition(check_function=is_tabbed),
        ],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),

    "update_anode_current_collector_design": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC],
        conditions=[
            TriggerCondition(check_function=has_type_changed)
        ],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_punched_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_PUNCHED],
        conditions=[
            TriggerCondition(check_function=has_changed),
            TriggerCondition(check_function=is_punched),
        ],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_notched_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_NOTCHED],
        conditions=[
            TriggerCondition(check_function=has_changed),
            TriggerCondition(check_function=is_notched),
        ],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_tabless_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_TABLESS],
        conditions=[
            TriggerCondition(check_function=has_changed),
            TriggerCondition(check_function=is_tabless),
        ],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_tabbed_current_collector": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_TABBED],
        conditions=[
            TriggerCondition(check_function=has_changed),
            TriggerCondition(check_function=is_tabbed),
        ],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),

    "update_cathode_current_collector_material": CallbackTriggerConfig(
        config=MATERIAL_CONFIGS[MaterialType.CATHODE_CURRENT_COLLECTOR],
        conditions=[
            TriggerCondition(check_function=has_changed),
        ],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_current_collector_material": CallbackTriggerConfig(
        config=MATERIAL_CONFIGS[MaterialType.ANODE_CURRENT_COLLECTOR],
        conditions=[
            TriggerCondition(check_function=has_changed),
        ],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),

}

##############################
##### Helper Functions #######
##############################

def _evaluate_conditions(
    trigger_config: CallbackTriggerConfig,
    old_cell: Optional[object],
    new_cell: Optional[object]
) -> Dict[str, bool]:
    
    """Evaluate all conditions for a callback trigger."""
    
    conditions_dict = {}
    
    if trigger_config.conditions:
        for condition in trigger_config.conditions:
            condition_result = condition.check_function(old_cell, new_cell, trigger_config.config)
            condition_name = getattr(condition, 'name', condition.check_function.__name__)
            conditions_dict[condition_name] = condition_result
    
    return conditions_dict

def _should_fire_on_cell_load(
    trigger_config: CallbackTriggerConfig,
    old_cell: Optional[object],
    new_cell: Optional[object]
) -> bool:
    
    """Determine if callback should fire on cell load."""

    if not trigger_config.conditions:
        return True
    
    condition_results = _evaluate_conditions(trigger_config, old_cell, new_cell)

    return all(condition_results.values())

def _trigger_callback(callback_name: str, timestamp: float) -> None:
    """Trigger a callback by updating its trigger store."""
    print(f"############ Triggering {callback_name}... ################")
    set_props({"type": "trigger", "callback": callback_name}, {"data": timestamp})

##############################
##### Callback Triggers #####
##############################


@callback(
    [
        Input("cell_store", "data"),
        Input("old_cell_store", "data"),
        Input("cathode_current_collector_tab", "style"),
        Input("cathode_tab", "style"),
        Input("anode_current_collector_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
    ],
    [
        State("last_triggered", "data"),
    ],
    prevent_initial_call=True,
)
def orchestrate_current_collector_callbacks(
    cell_data: Dict,
    old_cell_data: Optional[Dict],
    cathode_cc_tab_style: Dict,
    cathode_tab_style: Dict,
    anode_cc_tab_style: Dict,
    anode_tab_style: Dict,
    tabs_panel_style: Dict,
    last_triggered_callback: str,
) -> None:
    """Orchestrate all current collector callbacks by updating their trigger stores."""
    print("Orchestrating current collector callbacks...")

    timestamp = time.time()
    
    # Get cells from cache
    new_cell = get_cell_from_cache(cell_data["cache_key"])
    old_cell = get_cell_from_cache(old_cell_data["cache_key"])

    # Create visibility context
    visibility_styles = {
        "cathode_current_collector_tab": cathode_cc_tab_style,
        "cathode_tab": cathode_tab_style,
        "anode_current_collector_tab": anode_cc_tab_style,
        "anode_tab": anode_tab_style,
        "tabs_panel": tabs_panel_style,
    }

    # Handle cell loaded case
    if last_triggered_callback == "Cell Loaded":
        for callback_name, trigger_config in COLLECTOR_TRIGGER_CONFIGS.items():
            if _should_fire_on_cell_load(trigger_config, old_cell, new_cell):
                print(f"############ Cell Loaded - Triggering {callback_name}... ################")
                _trigger_callback(callback_name, timestamp)
        return

    # Handle normal cases
    for callback_name, trigger_config in COLLECTOR_TRIGGER_CONFIGS.items():
        # Check visibility
        required_styles = [visibility_styles.get(element_id) for element_id in trigger_config.required_visibility]
        visibility_condition = is_visible(required_styles)
        
        # Check anti-circular logic
        anti_circular_condition = last_triggered_callback != callback_name
        
        # Check callback-specific conditions
        callback_conditions = _evaluate_conditions(trigger_config, old_cell, new_cell)
        
        # Combine all conditions
        all_conditions = {
            "visibility": visibility_condition,
            "anti_circular": anti_circular_condition,
            **callback_conditions
        }
        
        print(f"callback name: {callback_name}, conditions: {all_conditions}")
        
        # Trigger if all conditions are met
        if all(all_conditions.values()):
            _trigger_callback(callback_name, timestamp)

