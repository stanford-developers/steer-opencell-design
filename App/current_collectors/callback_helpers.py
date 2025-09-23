from typing import Type, List, Tuple
from dash import no_update, ctx
import time

from steer_opencell_design.Components.CurrentCollectors import *

from App.general.callback_helpers import create_no_update_response
from App.general.enumerated_classes import *
from App.general.cell_operations import get_cell_from_cache, get_object_from_cell
from App.general.trigger_router import TriggerRouter, TriggerType
from App.general.handlers import handle_cell_store_update, handle_property_update

from App.current_collectors.configs import COLLECTOR_CONFIGS


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
        textitem_values=None,  # Add this parameter
        viewing_styles=[],
    ) -> Tuple:
        # Get the triggered ID
        triggered_id = ctx.triggered_id

        # get the propid
        triggered_prop_id = list(ctx.triggered_prop_ids.keys())[0].split(".")[-1]

        # If all display is none for any of the viewing styles, return no update
        if any(d.get("display") == "none" for d in viewing_styles):
            return create_no_update_response(config, existing_warnings)

        # Get the cell from cache
        cell = get_cell_from_cache(cell_data["cache_key"])

        # get the current collector from the cell, either cathode or anode depending on electrode
        current_collector = get_object_from_cell(cell, config)

        # no response if the current collector type does not match the expected type
        if config.collector_type != type(current_collector):
            return create_no_update_response(config, existing_warnings)

        # Map the triggered ID to the appropriate action using ENUMS
        trigger_type = TriggerRouter.get_trigger_type(triggered_id, triggered_prop_id)

        if trigger_type == TriggerType.CELL_STORE or trigger_type == TriggerType.STYLE:
            return handle_cell_store_update(
                current_collector, config, existing_warnings
            )

        elif trigger_type == TriggerType.PROPERTY:
            return handle_property_update(
                existing_warnings,
                triggered_id,
                cell,
                current_collector,
                config,
                input_values,
                slider_values,
                range_slider_values,
                input_start_values,
                input_end_values,
                radioitem_values,
                textitem_values,
            )

        return create_no_update_response(config, existing_warnings)

    return generic_update_current_collector


def convert_current_collector(current_collector: Type, target_type_name: str):
    """Convert current collector from one type to another using from_* constructors."""

    # Get the current type name
    current_type_name = type(current_collector).__name__

    # Define conversion methods for each source -> target combination
    conversion_map = {
        # From NotchedCurrentCollector
        (
            "NotchedCurrentCollector",
            "TablessCurrentCollector",
        ): lambda cc: TablessCurrentCollector.from_notched(cc),
        (
            "NotchedCurrentCollector",
            "TabWeldedCurrentCollector",
        ): lambda cc: TabWeldedCurrentCollector.from_notched(cc),
        # From TablessCurrentCollector
        (
            "TablessCurrentCollector",
            "NotchedCurrentCollector",
        ): lambda cc: NotchedCurrentCollector.from_tabless(cc),
        (
            "TablessCurrentCollector",
            "TabWeldedCurrentCollector",
        ): lambda cc: TabWeldedCurrentCollector.from_tabless(cc),
        # From TabWeldedCurrentCollector
        (
            "TabWeldedCurrentCollector",
            "NotchedCurrentCollector",
        ): lambda cc: NotchedCurrentCollector.from_tab_welded(cc),
        (
            "TabWeldedCurrentCollector",
            "TablessCurrentCollector",
        ): lambda cc: TablessCurrentCollector.from_tab_welded(cc),
    }

    # Generate the conversion key
    conversion_key = (current_type_name, target_type_name)

    # create the function to convert
    converter = conversion_map[conversion_key]

    # create the new current collector using the converter
    new_current_collector = converter(current_collector)

    return new_current_collector
