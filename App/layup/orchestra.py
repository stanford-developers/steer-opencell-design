from dash import html, callback, Input, State
from typing import Dict, Optional
import time

from App.general.orchestra import (
    has_changed, 
    create_trigger_store,
    orchestrate_callbacks_generic,
    CallbackTriggerConfig, 
    TriggerCondition,
)
from App.layup.configs import LAYUP_CONFIGS, LayupType

##############################
####### Trigger Stores #######
##############################

# Define callback names as constants
LAYUP_CALLBACKS = [
    "update_layup_dropdown_options",
    "update_layup_design_parameters_layout",
]

ALL_CALLBACKS = LAYUP_CALLBACKS

layup_trigger_stores = html.Div([create_trigger_store(callback_name) for callback_name in ALL_CALLBACKS])

##############################
##### Trigger Configs ########
##############################

LAYUP_TRIGGER_CONFIGS = {

    "update_layup_dropdown_options": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.GENERIC],
        conditions=[
            TriggerCondition(check_function=has_changed)
        ],
        required_visibility=[
            "layup_mechanicals_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),

    "update_layup_design_parameters_layout": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.GENERIC],
        conditions=[
            TriggerCondition(check_function=has_changed)
        ],
        required_visibility=[
            "layup_mechanicals_layout",
            "layup_tab",
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
        Input("layup_mechanicals_layout", "style"),
        Input("layup_tab", "style"),
        Input("tabs_panel", "style"),
    ],
    [
        State("last_triggered", "data"),
    ],
    prevent_initial_call=True,
)
def orchestrate_layup_callbacks(
    cell_data: Dict,
    old_cell_data: Optional[Dict],
    layup_mechanicals_layout_style: Dict,
    layup_tab_style: Dict,
    tabs_panel_style: Dict,
    last_triggered_callback: str,
) -> None:
    """Orchestrate all layup callbacks by updating their trigger stores."""
    
    timestamp = time.time()
    
    # Create visibility context
    visibility_styles = {
        "layup_mechanicals_layout": layup_mechanicals_layout_style,
        "layup_tab": layup_tab_style,
        "tabs_panel": tabs_panel_style,
    }

    # Use generic orchestration function
    orchestrate_callbacks_generic(
        trigger_configs=LAYUP_TRIGGER_CONFIGS,
        cell_data=cell_data,
        old_cell_data=old_cell_data,
        visibility_styles=visibility_styles,
        last_triggered_callback=last_triggered_callback,
        timestamp=timestamp,
        debug_name="Layup"
    )

