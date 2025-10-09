from dash import html, callback, Input, State
from typing import Dict, Optional
import time

from App.general.orchestra import (
    create_trigger_store,
    orchestrate_callbacks_generic,
    CallbackTriggerConfig, 
)

from App.formulations.configs import FORMULATION_CONFIGS, FormulationType


##############################
####### Trigger Stores #######
##############################

# Define callback names as constants
FORMULATION_CALLBACKS = [
    "update_cathode_formulation_main",
    "update_anode_formulation_main",
    "update_cathode_formulation_div",
    "update_anode_formulation_div",
]

ALL_CALLBACKS = FORMULATION_CALLBACKS

formulation_trigger_stores = html.Div([create_trigger_store(callback_name) for callback_name in ALL_CALLBACKS])


##############################
##### Trigger Configs ########
##############################

FORMULATION_TRIGGER_CONFIGS = {

    "update_cathode_formulation_main": CallbackTriggerConfig(
        config=FORMULATION_CONFIGS[FormulationType.CATHODE],
        conditions=[],
        required_visibility=[
            "cathode_formulation_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),

    "update_anode_formulation_main": CallbackTriggerConfig(
        config=FORMULATION_CONFIGS[FormulationType.ANODE],
        conditions=[],
        required_visibility=[
            "anode_formulation_tab",
            "anode_tab",
            "tabs_panel"
        ]
    ),

    "update_cathode_formulation_div": CallbackTriggerConfig(
        config=FORMULATION_CONFIGS[FormulationType.CATHODE],
        conditions=[],
        required_visibility=[
            "cathode_formulation_tab",
            "cathode_tab",
            "tabs_panel"
        ]
    ),

    "update_anode_formulation_div": CallbackTriggerConfig(
        config=FORMULATION_CONFIGS[FormulationType.ANODE],
        conditions=[],
        required_visibility=[
            "anode_formulation_tab",
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
        Input("cathode_formulation_tab", "style"),
        Input("anode_formulation_tab", "style"),
        Input("cathode_tab", "style"),
        Input("anode_tab", "style"),
        Input("tabs_panel", "style"),
    ],
    [
        State("last_triggered", "data"),
    ],
    prevent_initial_call=True,
)
def orchestrate_formulation_callbacks(
    cell_data: Dict,
    old_cell_data: Optional[Dict],
    cathode_formulation_tab_style: Dict,
    anode_formulation_tab_style: Dict,
    cathode_tab_style: Dict,
    anode_tab_style: Dict,
    tabs_panel_style: Dict,
    last_triggered_callback: str,
) -> None:
    
    """Orchestrate all formulation callbacks by updating their trigger stores."""
    
    timestamp = time.time()
    
    # Create visibility context
    visibility_styles = {
        "cathode_formulation_tab": cathode_formulation_tab_style,
        "anode_formulation_tab": anode_formulation_tab_style,
        "cathode_tab": cathode_tab_style,
        "anode_tab": anode_tab_style,
        "tabs_panel": tabs_panel_style,
    }

    # Use generic orchestration function
    orchestrate_callbacks_generic(
        trigger_configs=FORMULATION_TRIGGER_CONFIGS,
        cell_data=cell_data,
        old_cell_data=old_cell_data,
        visibility_styles=visibility_styles,
        last_triggered_callback=last_triggered_callback,
        timestamp=timestamp,
        debug_name="Formulation"
    )

