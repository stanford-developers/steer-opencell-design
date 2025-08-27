from typing import Type, List, Tuple
from dash import no_update, ctx
import time

from steer_opencell_design.Formulations.ElectrodeFormulations import *

from App.general.callback_helpers import create_no_update_response
from App.general.enumerated_classes import *
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.handlers import handle_cell_store_update, handle_property_update

from App.formulations.configs import FORMULATION_CONFIGS


def create_generic_formulation_callback(formulation_type: FormulationType) -> callable:
    """Factory function to create formulation callbacks."""
    
    config = FORMULATION_CONFIGS[formulation_type]
    
    def generic_update_formulation(
        existing_warnings,
        cell_data, 
        input_values, 
        slider_values, 
    ) -> Tuple:

        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data['cache_key'])

        # get the formulation from the cell
        formulation = get_object_from_cell(cell, config)

        # Create trigger router and process the trigger
        trigger_type = TriggerRouter.get_trigger_type(triggered_id)

        if trigger_type == TriggerType.CELL_STORE:
            return handle_cell_store_update(
                formulation,
                config,
                existing_warnings
            )

        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(
                existing_warnings,
                triggered_id,
                cell,
                formulation,
                config,
                input_values,
                slider_values,
            )

        # Default: return no update for all outputs
        return create_no_update_response(len(config.parameter_list))

    return generic_update_formulation
