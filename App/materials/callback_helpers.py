from dash import no_update, ctx
from typing import Tuple, Type
from current_collectors.lists import CC_MATERIAL_PARAMETER_LIST
from general.enumerated_classes import TriggerType
from general.trigger_router import TriggerRouter
from general.cell_operations import get_cell_from_cache


def create_material_callback(material_type: Type) -> callable:
    """Factory for creating material update callbacks."""

    def update_material(cell_data, material_name, input_values, slider_values, drag_values, slider_steps, input_steps):

        from materials.handlers import (
            handle_cell_store_update, 
            handle_selector_update, 
            handle_property_update,
            handle_drag_value_update
        )

        from current_collectors.callback_helpers import create_no_update_response

        # get the triggered ID
        triggered_id = ctx.triggered_id

        # get the component property that triggered it
        prop_id = ctx.triggered[0]['prop_id'].split('.')[-1]

        if prop_id == 'drag_value':
            return handle_drag_value_update(triggered_id, drag_values, slider_steps, input_steps, input_values)

        # get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # Get the trigger type using the TriggerRouter
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        if trigger_type == TriggerType.CELL_STORE:
            return handle_cell_store_update(cell, material_type)

        elif trigger_type == TriggerType.COMPONENT_SELECTOR:
            return handle_selector_update(material_name, cell, material_type)

        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(triggered_id, cell, material_type, input_values, slider_values)

        return create_no_update_response()

    return update_material


def create_no_update_response() -> Tuple:
    """Create a no_update response specifically for material callbacks."""
    num_material_params = len(CC_MATERIAL_PARAMETER_LIST)  
    
    return (
        no_update,  # cache_key
        no_update,  # material_selector value
        [no_update] * num_material_params,  # slider values
        [no_update] * num_material_params,  # slider mins
        [no_update] * num_material_params,  # slider maxs
        [no_update] * num_material_params,  # slider marks
        [no_update] * num_material_params,  # slider steps
        [no_update] * num_material_params,  # input values
        [no_update] * num_material_params,  # input steps
    )

