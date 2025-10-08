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
from App.electrodes.configs import ELECTRODE_CONFIGS, ElectrodeType
from App.layup.configs import LAYUP_CONFIGS, LayupType

##############################
####### Trigger Stores #######
##############################

# Define callback names as constants
MECHANICALS_CALLBACKS = [
    "update_cathode_mechanicals_plots",
    "update_anode_mechanicals_plots",
]

LOAD_BALANCING_CALLBACKS = [
    "update_cathode_cross_section",
    "update_anode_cross_section",
    "update_areal_capacity_plot",
]

ALL_CALLBACKS = MECHANICALS_CALLBACKS + LOAD_BALANCING_CALLBACKS

results_trigger_stores = html.Div([create_trigger_store(callback_name) for callback_name in ALL_CALLBACKS])

##############################
##### Trigger Configs ########
##############################

RESULTS_TRIGGER_CONFIGS = {

    "update_cathode_mechanicals_plots": CallbackTriggerConfig(
        config=ELECTRODE_CONFIGS[ElectrodeType.CATHODE],
        conditions=[
            TriggerCondition(check_function=has_changed)
        ],
        required_visibility=[
            "mechanicals_tab",
            "tabs_panel"
        ]
    ),

    "update_anode_mechanicals_plots": CallbackTriggerConfig(
        config=ELECTRODE_CONFIGS[ElectrodeType.ANODE],
        conditions=[
            TriggerCondition(check_function=has_changed)
        ],
        required_visibility=[
            "mechanicals_tab",
            "tabs_panel"
        ]
    ),

    "update_cathode_cross_section": CallbackTriggerConfig(
        config=ELECTRODE_CONFIGS[ElectrodeType.CATHODE],
        required_visibility=[
            "load_balancing_tab",
            "tabs_panel"
        ]
    ),

    "update_anode_cross_section": CallbackTriggerConfig(
        config=ELECTRODE_CONFIGS[ElectrodeType.ANODE],
        required_visibility=[
            "load_balancing_tab",
            "tabs_panel"
        ]
    ),

    "update_areal_capacity_plot": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.GENERIC],
        conditions=[
            TriggerCondition(check_function=has_changed)
        ],
        required_visibility=[
            "load_balancing_tab",
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
        Input("mechanicals_tab", "style"),
        Input("load_balancing_tab", "style"),
        Input("tabs_panel", "style"),
    ],
    [
        State("last_triggered", "data"),
    ],
    prevent_initial_call=True,
)
def orchestrate_results_callbacks(
    cell_data: Dict,
    old_cell_data: Optional[Dict],
    mechanicals_tab_style: Dict,
    load_balancing_tab_style: Dict,
    tabs_panel_style: Dict,
    last_triggered_callback: str,
) -> None:
    """Orchestrate all results callbacks by updating their trigger stores."""
    
    timestamp = time.time()
    
    # Create visibility context
    visibility_styles = {
        "mechanicals_tab": mechanicals_tab_style,
        "load_balancing_tab": load_balancing_tab_style,
        "tabs_panel": tabs_panel_style,
    }

    # Use generic orchestration function
    orchestrate_callbacks_generic(
        trigger_configs=RESULTS_TRIGGER_CONFIGS,
        cell_data=cell_data,
        old_cell_data=old_cell_data,
        visibility_styles=visibility_styles,
        last_triggered_callback=last_triggered_callback,
        timestamp=timestamp,
        debug_name="Results"
    )

