from dash import html, dcc, callback, Input, State, set_props
from typing import Dict, Optional, List
import time

from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.electrodes.configs import ELECTRODE_CONFIGS, ElectrodeType
from App.current_collectors.configs import COLLECTOR_CONFIGS, CollectorType
from App.materials.configs import MATERIAL_CONFIGS, MaterialType
from App.general.orchestra import (
    has_type_changed,
    create_trigger_store,
    orchestrate_callbacks_generic,
    CallbackTriggerConfig, 
    TriggerCondition,
)

##############################
####### Trigger Stores #######
##############################

CATHODE_CALLBACKS = [
    "toggle_cathode_insulation_parameters_style",
    "update_cathode_current_collector_insulation_material",
    "update_cathode",
]

ANODE_CALLBACKS = [
    "toggle_anode_insulation_parameters_style",
    "update_anode_current_collector_insulation_material",
    "update_anode",
]

ALL_CALLBACKS = CATHODE_CALLBACKS + ANODE_CALLBACKS

# create the stores
electrode_trigger_stores = html.Div([create_trigger_store(callback_name) for callback_name in ALL_CALLBACKS])


##############################
##### Trigger Configs ########
##############################

ELECTRODE_TRIGGER_CONFIGS = {

    "toggle_cathode_insulation_parameters_style": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC],
        conditions=[],
        required_visibility=[
            "cathode_electrode_tab",
            "cathode_tab", 
            "tabs_panel"
        ]
    ),
    "update_cathode_current_collector_insulation_material": CallbackTriggerConfig(
        config=MATERIAL_CONFIGS[MaterialType.CATHODE_INSULATION],
        conditions=[],
        required_visibility=[
            "cathode_electrode_tab",
            "cathode_tab", 
            "tabs_panel"
        ]
    ),

    "toggle_anode_insulation_parameters_style": CallbackTriggerConfig(
        config=COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC],
        conditions=[],
        required_visibility=[
            "anode_electrode_tab",
            "anode_tab", 
            "tabs_panel"
        ]
    ),
    "update_anode_current_collector_insulation_material": CallbackTriggerConfig(
        config=MATERIAL_CONFIGS[MaterialType.ANODE_INSULATION],
        conditions=[],
        required_visibility=[
            "anode_electrode_tab",
            "anode_tab", 
            "tabs_panel"
        ]
    ),

    "update_cathode": CallbackTriggerConfig(
        config=ELECTRODE_CONFIGS[ElectrodeType.CATHODE],
        conditions=[],
        required_visibility=[
            "cathode_electrode_tab",
            "cathode_tab", 
            "tabs_panel"
        ]
    ),

    "update_anode": CallbackTriggerConfig(
        config=ELECTRODE_CONFIGS[ElectrodeType.ANODE],
        conditions=[],
        required_visibility=[
            "anode_electrode_tab",
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
        Input("cathode_electrode_tab", "style"),
        Input("cathode_tab", "style"),
        Input("anode_electrode_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
    ],
    [
        State("last_triggered", "data"),
    ],
    prevent_initial_call=True,
)
def orchestrate_electrode_callbacks(
    cell_data: Dict,
    old_cell_data: Optional[Dict],
    cathode_electrode_tab_style: Dict,
    cathode_tab_style: Dict,
    anode_electrode_tab_style: Dict,
    anode_tab_style: Dict,
    tabs_panel_style: Dict,
    last_triggered_callback: str,
) -> None:
    """Orchestrate all electrode callbacks by updating their trigger stores."""

    timestamp = time.time()
    
    # Create visibility context
    visibility_styles = {
        "cathode_electrode_tab": cathode_electrode_tab_style,
        "cathode_tab": cathode_tab_style,
        "anode_electrode_tab": anode_electrode_tab_style,
        "anode_tab": anode_tab_style,
        "tabs_panel": tabs_panel_style,
    }

    # Use generic orchestration function
    orchestrate_callbacks_generic(
        trigger_configs=ELECTRODE_TRIGGER_CONFIGS,
        cell_data=cell_data,
        old_cell_data=old_cell_data,
        visibility_styles=visibility_styles,
        last_triggered_callback=last_triggered_callback,
        timestamp=timestamp,
        debug_name="Electrodes"
    )

