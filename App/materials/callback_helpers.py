from dash import no_update, ctx
from typing import Tuple, Type

from materials.configs import MATERIAL_CONFIGS

from general.enumerated_classes import TriggerType, MaterialType
from general.trigger_router import TriggerRouter
from general.cell_operations import get_cell_from_cache, get_object_from_cell
from general.callback_helpers import create_no_update_response


def create_material_callback(material_type: MaterialType) -> callable:

    config = MATERIAL_CONFIGS[material_type]

    def update_material(existing_warnings, cell_data, material_name, input_values, slider_values):

        from materials.handlers import handle_selector_update
        from general.handlers import handle_cell_store_update, handle_property_update

        # get the triggered ID
        triggered_id = ctx.triggered_id

        # get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # get the current collector from the cell, either cathode or anode depending on electrode
        try:
            material = get_object_from_cell(cell, config)
        except Exception as e:
            return create_no_update_response(config, existing_warnings)

        # Get the trigger type using the TriggerRouter
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        if trigger_type == TriggerType.CELL_STORE:
            return handle_cell_store_update(material, config, existing_warnings)

        elif trigger_type == TriggerType.COMPONENT_SELECTOR:
            return handle_selector_update(material_name, cell, config, existing_warnings)

        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(existing_warnings, triggered_id, cell, material, config, input_values, slider_values)

        return create_no_update_response(config)

    return update_material

