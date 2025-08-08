from dash import no_update

from typing import Type, Tuple

from general.callback_helpers import validate_dependent_properties, generate_parameters
from general.enumerated_classes import SubType
from general.callback_helpers import set_cell_to_cache
from steer_core.Apps.ContextManagers import capture_warnings

from electrodes.cell_operations import set_electrode_to_cell
from electrodes.parameter_lists import ELECTRODE_SETTABLE_PARAMETERS, ELECTRODE_PARAMETER_LIST


def handle_cell_store_update(object: Type, existing_warnings: list) -> Tuple:
    """Handle cell store update for any collector type."""
    
    # IMPORTANT: Validate all dependent properties first
    validate_dependent_properties(
        object,
        ELECTRODE_SETTABLE_PARAMETERS,
        None
    )
    
    # Generate basic parameters
    value_list, min_values, max_values, marks_list = generate_parameters(
        object, 
        ELECTRODE_PARAMETER_LIST
    )
    
    # Start building response
    response = (
        no_update,
        value_list,
        value_list,
        min_values,
        max_values,
        min_values,
        max_values,
        marks_list,
        existing_warnings
    )

    return response


def handle_property_update(
    triggered_id: dict,
    electrode: Type,
    cell: Type,
    input_values: list,
    slider_values: list,
    existing_warnings: list
) -> Tuple:
    """Handle property updates for any electrode type."""
    
    property_name = triggered_id['property']
    subtype = SubType(triggered_id['subtype']) 

    property_index = ELECTRODE_PARAMETER_LIST.index(property_name)
    if subtype == SubType.SLIDER:
        value = slider_values[property_index]
    elif subtype == SubType.INPUT:
        value = input_values[property_index]

    with capture_warnings(existing_warnings, f"electrode.{property_name}") as all_warnings:
        setattr(electrode, property_name, value)

    # Validate dependent properties
    validate_dependent_properties(electrode, ELECTRODE_SETTABLE_PARAMETERS, property_name)
    
    # Generate updated parameters
    from current_collectors.callback_helpers import generate_parameters
    value_list, min_values, max_values, marks_list = generate_parameters(
        electrode, ELECTRODE_PARAMETER_LIST
    )
    
    # Update cell
    new_cell = set_electrode_to_cell(cell, electrode)
    
    # Update cache
    new_key = set_cell_to_cache(new_cell)

    # Build response
    response = (
        {'cache_key': new_key},
        value_list,
        value_list,
        min_values,
        max_values,
        min_values,
        max_values,
        marks_list,
        all_warnings
    )

    return response


def handle_flip_action():
    pass

