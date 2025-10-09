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
from App.general.cell_operations import get_object_from_cell
from App.layup.configs import LAYUP_CONFIGS, LayupType
from App.materials.configs import MATERIAL_CONFIGS, MaterialType

from steer_opencell_design.Constructions.Layups import (
    Laminate,
    MonoLayer,
    ZFoldMonoLayer,
)

##############################
####### Trigger Stores #######
##############################

# Define callback names as constants
LAYUP_CALLBACKS = [
    "update_layup_dropdown_options",
    "update_layup_design_parameters_layout",
    "update_zfold_monolayer",
    "update_laminate", 
    "update_monolayer",
    "update_separator_material",
    "update_zfold_monolayer_separator",
    "update_laminate_top_separator",
    "update_laminate_bottom_separator",
    "update_stacked_top_separator",
    "update_stacked_bottom_separator",
    "update_generic_layup",
]

ALL_CALLBACKS = LAYUP_CALLBACKS

layup_trigger_stores = html.Div([create_trigger_store(callback_name) for callback_name in ALL_CALLBACKS])

##############################
##### Trigger Conditions #####
##############################

def is_laminate(old_cell, new_cell, config: LayupType) -> bool:
    """Check if layup is laminate type."""
    layup = get_object_from_cell(new_cell, config)
    return type(layup) == Laminate

def is_monolayer(old_cell, new_cell, config: LayupType) -> bool:
    """Check if layup is monolayer type."""
    layup = get_object_from_cell(new_cell, config)
    return type(layup) == MonoLayer

def is_zfold(old_cell, new_cell, config: LayupType) -> bool:
    """Check if layup is z-fold monolayer type."""
    layup = get_object_from_cell(new_cell, config)
    return type(layup) == ZFoldMonoLayer

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
    "update_zfold_monolayer": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.ZFOLDMONOLAYER],
        conditions=[
            TriggerCondition(check_function=is_zfold),
        ],
        required_visibility=[
            "layup_overhangs_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),
    "update_laminate": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.LAMINATE],
        conditions=[
            TriggerCondition(check_function=is_laminate),
        ],
        required_visibility=[
            "layup_overhangs_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),
    "update_monolayer": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.MONOLAYER],
        conditions=[
            TriggerCondition(check_function=is_monolayer),
        ],
        required_visibility=[
            "layup_overhangs_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),

    "update_separator_material": CallbackTriggerConfig(
        config=MATERIAL_CONFIGS[MaterialType.SEPARATOR_MATERIAL],
        conditions=[
            TriggerCondition(check_function=has_changed)
        ],
        required_visibility=[
            "layup_mechanicals_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),
    "update_zfold_monolayer_separator": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.ZFOLDMONOLAYER],
        conditions=[
            TriggerCondition(check_function=is_zfold),
        ],
        required_visibility=[
            "layup_mechanicals_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),
    "update_laminate_top_separator": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.LAMINATE],
        conditions=[
            TriggerCondition(check_function=is_laminate),
        ],
        required_visibility=[
            "layup_mechanicals_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),
    "update_laminate_bottom_separator": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.LAMINATE],
        conditions=[
            TriggerCondition(check_function=is_laminate),
        ],
        required_visibility=[
            "layup_mechanicals_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),
    "update_stacked_top_separator": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.MONOLAYER],
        conditions=[
            TriggerCondition(check_function=is_monolayer),
        ],
        required_visibility=[
            "layup_mechanicals_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),

    "update_stacked_bottom_separator": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.MONOLAYER],
        conditions=[
            TriggerCondition(check_function=is_monolayer),
        ],
        required_visibility=[
            "layup_mechanicals_layout",
            "layup_tab",
            "tabs_panel"
        ]
    ),

    "update_generic_layup": CallbackTriggerConfig(
        config=LAYUP_CONFIGS[LayupType.GENERIC],
        conditions=[],
        required_visibility=[
            "layup_areal_layout",
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
        Input("layup_overhangs_layout", "style"),
        Input("layup_areal_layout", "style"),
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
    layup_overhangs_layout_style: Dict,
    layup_areal_layout_style: Dict,
    layup_tab_style: Dict,
    tabs_panel_style: Dict,
    last_triggered_callback: str,
) -> None:
    """Orchestrate all layup callbacks by updating their trigger stores."""
    
    timestamp = time.time()
    
    # Create visibility context
    visibility_styles = {
        "layup_mechanicals_layout": layup_mechanicals_layout_style,
        "layup_overhangs_layout": layup_overhangs_layout_style,
        "layup_areal_layout": layup_areal_layout_style,
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

