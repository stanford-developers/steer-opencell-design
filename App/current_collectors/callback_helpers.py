from typing import Type, List, Tuple
from dash import no_update, ctx
import time
from dash.exceptions import PreventUpdate

from steer_opencell_design.Components.CurrentCollectors import *

from App.general.enumerated_classes import *
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.handlers import handle_cell_store_update, handle_property_update

from App.current_collectors.configs import COLLECTOR_CONFIGS, CollectorType
from App.current_collectors.handlers import handle_cell_store_cc_design_dropdown, handle_dropdown_cc_design_dropdown


def create_generic_current_collector_callback(
    collector_type: CollectorType,
) -> callable:
    """Factory function to create current collector callbacks."""

    config = COLLECTOR_CONFIGS[collector_type]

    def generic_update_current_collector(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        range_slider_values=None,
        input_start_values=None,
        input_end_values=None,
        radioitem_values=None,
        textitem_values=None,
        original_values=None,
        original_mins=None,
        original_maxs=None,
        original_slider_marks=None,
        original_slider_steps=None,
        original_input_steps=None,
        original_rangeslider_values=None,
        original_rangeslider_mins=None,
        original_rangeslider_maxs=None,
        original_rangeslider_marks=None,
        original_rangeslider_steps=None,
        original_input_start_steps=None,
        original_input_end_steps=None
    ) -> Tuple:
        
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # Get the cell from cache
        cache_key = cell_data["cache_key"]
        cell = get_cell_from_cache(cache_key)

        # get the current collector from the cell, either cathode or anode depending on electrode
        current_collector = get_object_from_cell(cell, config)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_update(current_collector, config, existing_warnings)

        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(
                existing_warnings,
                triggered_id,
                cell,
                cache_key,
                current_collector,
                config,
                input_values,
                slider_values,
                range_slider_values,
                input_start_values,
                input_end_values,
                radioitem_values,
                textitem_values,
                original_values,
                original_mins,
                original_maxs,
                original_slider_marks,
                original_slider_steps,
                original_input_steps,
                original_rangeslider_values,
                original_rangeslider_mins,
                original_rangeslider_maxs,
                original_rangeslider_marks,
                original_rangeslider_steps,
                original_input_start_steps,
                original_input_end_steps,
            )

        raise PreventUpdate

    return generic_update_current_collector


def create_dropdown_options_callback(collector_type: CollectorType) -> callable:
    
    config = COLLECTOR_CONFIGS[collector_type]

    def callback_function(
        cell_data, 
        dropdown_value,
        current_dropdown_style,
        punched_style,
        notched_style,
        tabless_style,
        tabbed_style
    ):
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # get the cell from the cache
        cell = get_cell_from_cache(cell_data["cache_key"])

        # get the current collector from the cell
        current_collector = get_object_from_cell(cell, config)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_cc_design_dropdown(
                current_collector,
                current_dropdown_style,
                punched_style,
                notched_style,
                tabless_style,
                tabbed_style
            )
        
        elif trigger_type == TriggerType.DROPDOWN:
            return handle_dropdown_cc_design_dropdown(
                cell,
                current_collector,
                dropdown_value,
                config,
                current_dropdown_style,
                punched_style,
                notched_style,
                tabless_style,
                tabbed_style
            )
        
        raise PreventUpdate
    
    return callback_function

