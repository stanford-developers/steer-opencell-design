from dash import ctx
from typing import Tuple, Type
from dash.exceptions import PreventUpdate

from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.handlers import handle_cell_store_update, handle_property_update
from App.general.callback_helpers import prevent_update_from_styles

from App.electrodes.configs import ELECTRODE_CONFIGS, ElectrodeType


def create_electrode_callback(electrode_key: ElectrodeType) -> callable:
    """Factory function to create electrode callbacks."""

    config = ELECTRODE_CONFIGS[electrode_key]

    def generic_update_electrode(
        existing_warnings: list,
        cell_data: dict,
        input_values: list,
        slider_values: list,
        viewing_styles=[],
        control_mode_values=None,
        original_values=None,
        original_mins=None,
        original_maxs=None,
        original_slider_marks=None,
        original_slider_steps=None,
        original_input_steps=None
    ) -> Tuple:
        
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # If all display is none for any of the viewing styles, return no update
        prevent_update_from_styles(viewing_styles)

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data["cache_key"])

        # get the electrode from the cell, either cathode or anode depending on electrode
        electrode = get_object_from_cell(cell, config)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        # trigger if the cell store is updated
        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_update(electrode, config, existing_warnings)

        # trigger if a property is updated
        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(
                existing_warnings=existing_warnings,
                triggered_id=triggered_id,
                cell=cell,
                object_instance=electrode,
                config=config,
                input_values=input_values,
                slider_values=slider_values,
                radioitem_values=control_mode_values,
                original_values=original_values,
                original_mins=original_mins,
                original_maxs=original_maxs,
                original_slider_marks=original_slider_marks,
                original_slider_steps=original_slider_steps,
                original_input_steps=original_input_steps
            )
        
        # Fallback
        raise PreventUpdate

    return generic_update_electrode
