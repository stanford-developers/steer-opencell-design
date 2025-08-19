from dash import ctx, no_update
from typing import Tuple, Type

from App.general.enumerated_classes import ElectrodeType
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.handlers import handle_cell_store_update, handle_property_update
from App.general.callback_helpers import create_no_update_response

from App.electrodes.configs import ELECTRODE_CONFIGS


def create_electrode_callback(electrode_key: ElectrodeType) -> callable:
    """Factory function to create electrode callbacks."""

    config = ELECTRODE_CONFIGS[electrode_key]

    def generic_update_electrode(
        existing_warnings: list,
        cell_data: dict, 
        input_values: list, 
        slider_values: list, 
    ) -> Tuple:
        
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # get the electrode from the cell, either cathode or anode depending on electrode
        electrode = get_object_from_cell(cell, config)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        # trigger if the cell store is updated
        if trigger_type == TriggerType.CELL_STORE:
            return handle_cell_store_update(electrode, config, existing_warnings)
        
        # trigger if a property is updated
        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(existing_warnings, triggered_id, cell, electrode, config, input_values, slider_values)

        # Fallback
        return create_no_update_response(config, existing_warnings)

    return generic_update_electrode

