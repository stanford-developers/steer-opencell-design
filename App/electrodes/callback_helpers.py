from dash import ctx, no_update
from typing import Tuple, Type

from general.enumerated_classes import ElectrodeType
from general.callback_helpers import get_cell_from_cache
from general.trigger_router import TriggerRouter, TriggerType

from electrodes.parameter_lists import ELECTRODE_PARAMETER_LIST, ELECTRODE_SETTABLE_PARAMETERS
from electrodes.electrode_handlers import handle_cell_store_update, handle_property_update, handle_flip_action


def create_no_update_response() -> Tuple:
    """Create a no_update response for a given electrode."""
    num_params = len(ELECTRODE_PARAMETER_LIST)
    
    response = [
        no_update,  # cache_key (single value)
        [no_update] * num_params,  # input values (list)
        [no_update] * num_params,  # slider values (list)
        [no_update] * num_params,  # slider mins (list)
        [no_update] * num_params,  # slider maxs (list)
        [no_update] * num_params,  # input mins (list)
        [no_update] * num_params,  # input maxs (list)
        [no_update] * num_params,  # marks (list)
    ]
    
    return tuple(response)


def create_electrode_callback(electrode_key: ElectrodeType) -> callable:
    """Factory function to create electrode callbacks."""
    
    def generic_update_electrode(
        cell_data: dict, 
        input_values: list, 
        slider_values: list, 
        flip_x: int, 
        flip_y: int,
        existing_warnings: list
    ) -> Tuple:
        
        from electrodes.cell_operations import get_electrode_from_cell

        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # get the electrode from the cell, either cathode or anode depending on electrode
        electrode = get_electrode_from_cell(cell, electrode_key)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        # trigger if the cell store is updated
        if trigger_type == TriggerType.CELL_STORE:
            return handle_cell_store_update(electrode, existing_warnings)
        
        # trigger if a property is updated
        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(triggered_id, electrode, cell, input_values, slider_values, existing_warnings)

        # trigger if an action is performed, e.g. flip
        elif trigger_type == TriggerType.ACTION:
            return handle_flip_action(triggered_id, electrode, cell, existing_warnings)
        
        # Fallback
        return create_no_update_response()

    return generic_update_electrode



