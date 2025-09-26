from steer_opencell_design.Components.CurrentCollectors import (
    _CurrentCollector,
    PunchedCurrentCollector,
    NotchedCurrentCollector,
    TablessCurrentCollector,
    TabWeldedCurrentCollector,
)

from App.current_collectors.configs import CurrentCollectorConfig
from App.general.cell_operations import set_cell_to_cache, set_object_to_cell

from dash import no_update
from typing import Type

def handle_cell_store_cc_design_dropdown(
    current_collector: _CurrentCollector,
    current_style: dict,
):

    from App.current_collectors.layouts import CURRENT_COLLECTOR_DESIGNS

    # Define type mappings
    type_config = {
        PunchedCurrentCollector: {
            "display": "none",
            "options": [{"label": "Punched", "value": "punched"}],
            "value": "punched",
        },
        NotchedCurrentCollector: {
            "display": "block",
            "options": [{"label": item, "value": item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != "Punched"],
            "value": "notched",
        },
        TablessCurrentCollector: {
            "display": "block",
            "options": [{"label": item, "value": item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != "Punched"],
            "value": "tabless",
        },
        TabWeldedCurrentCollector: {
            "display": "block",
            "options": [{"label": item, "value": item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != "Punched"],
            "value": "tabbed",
        },
    }

    # Get configuration for current collector type
    collector_type = type(current_collector)

    # get the configuration for the current collector type
    config = type_config.get(collector_type)

    # set the style according to the config display value
    current_style["display"] = config["display"]

    return no_update, config["options"], current_style, config["value"]


def handle_dropdown_cc_design_dropdown(
        cell: Type,
        current_collector: _CurrentCollector,
        dropdown_value: str,
        config: CurrentCollectorConfig
):
    
    # Map design values to collector types
    design_to_type = {
        "notched": "NotchedCurrentCollector",
        "tabless": "TablessCurrentCollector",
        "tabbed": "TabWeldedCurrentCollector",
    }

    # get the name of the target collector type
    target_type_name = design_to_type.get(dropdown_value)

    # Do the conversion
    new_collector = convert_current_collector(current_collector, target_type_name)

    # Assign the new current collector to the cell and get the key
    new_cell = set_object_to_cell(cell, new_collector, config)

    # Generate a new cache key
    new_key = set_cell_to_cache(new_cell)

    # Update the dash store with the new cell key
    return {"cache_key": new_key}, no_update, no_update, no_update


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

