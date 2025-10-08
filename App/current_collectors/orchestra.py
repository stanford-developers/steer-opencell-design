from dash import html, dcc, callback, Input, State, set_props
from typing import Dict, Optional, List
import time

from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.current_collectors.configs import COLLECTOR_CONFIGS, CollectorType
from App.materials.configs import MaterialType, MATERIAL_CONFIGS
from App.general.orchestra import (
    has_changed,
    has_type_changed,
    create_trigger_store,
    orchestrate_callbacks_generic,
    CallbackTriggerConfig, 
    TriggerCondition,
)

from steer_opencell_design.Components.CurrentCollectors import (
    PunchedCurrentCollector,
    NotchedCurrentCollector,
    TablessCurrentCollector,
    TabWeldedCurrentCollector,
)

##############################
####### Trigger Stores #######
##############################

CATHODE_CALLBACKS = [
    "update_cathode_current_collector_design",
    "update_cathode_punched_current_collector",
    "update_cathode_notched_current_collector",
    "update_cathode_tabless_current_collector",
    "update_cathode_tabbed_current_collector",
    "update_cathode_current_collector_material",
    "update_cathode_current_collector_tab_material",
]

ANODE_CALLBACKS = [
    "update_anode_current_collector_design",
    "update_anode_punched_current_collector",
    "update_anode_notched_current_collector",
    "update_anode_tabless_current_collector",
    "update_anode_tabbed_current_collector",
    "update_anode_current_collector_material",
    "update_anode_current_collector_tab_material",
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
        conditions=[],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),
    "update_cathode_current_collector_tab_material": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC],
        conditions=[
            TriggerCondition(check_function=is_tabbed),
        ],
        required_visibility=[
            "cathode_current_collector_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_current_collector_material": CallbackTriggerConfig(
        config=MATERIAL_CONFIGS[MaterialType.ANODE_CURRENT_COLLECTOR],
        conditions=[],
        required_visibility=[
            "anode_current_collector_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),
    "update_anode_current_collector_tab_material": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC],
        conditions=[
            TriggerCondition(check_function=is_tabbed),
        ],
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

    timestamp = time.time()
    
    # Create visibility context
    visibility_styles = {
        "cathode_current_collector_tab": cathode_cc_tab_style,
        "cathode_tab": cathode_tab_style,
        "anode_current_collector_tab": anode_cc_tab_style,
        "anode_tab": anode_tab_style,
        "tabs_panel": tabs_panel_style,
    }

    # Use generic orchestration function
    orchestrate_callbacks_generic(
        trigger_configs=COLLECTOR_TRIGGER_CONFIGS,
        cell_data=cell_data,
        old_cell_data=old_cell_data,
        visibility_styles=visibility_styles,
        last_triggered_callback=last_triggered_callback,
        timestamp=timestamp,
        debug_name="Current Collectors"
    )

