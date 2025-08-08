from typing import Type, Tuple, List
from dash import no_update

from current_collectors.parameter_lists import CC_MATERIAL_PARAMETER_LIST
from current_collectors.callback_helpers import create_material_no_update_response
from App.current_collectors.cell_operations import get_material_from_cell, set_material_to_cell
from general.enumerated_classes import MaterialType, SubType
from general.callback_helpers import generate_parameters, set_cell_to_cache
from steer_opencell_design.Components.CurrentCollectors import CurrentCollectorMaterial



def handle_cell_store_update(
    cell: Type,
    material_type: MaterialType
) -> Tuple:
    
    # get the material from the cell
    material = get_material_from_cell(material_type, cell)

    # If material doesn't exist (e.g., tab material on non-tabbed collector), return no_update
    if material is None:
        return create_material_no_update_response()

    # get the parameters for the material
    parameter_list, min_values, max_values, marks_list = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)
    
    # return the no_update response with the material name and parameters
    return (no_update, material.name, parameter_list, parameter_list, min_values, max_values, marks_list)

def handle_selector_update(
    material_name: str,
    cell: Type,
    material_type: MaterialType
) -> Tuple:
    """
    Handle updates to the material selector.

    Parameters
    ----------
    material_selector : str
        The selected material name from the dropdown.
    cell : Type
        The current cell object from the cache.
    material_type : MaterialType
        The type of material being updated (e.g., CATHODE_CURRENT_COLLECTOR_TAB).
    """
    # get the material from the database using the selector
    material = CurrentCollectorMaterial.from_database(material_name)

    # get the parameters for the material
    parameter_list, min_values, max_values, marks_list = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)

    # set the material to the cell
    new_cell = set_material_to_cell(material_type, cell, material)
    
    # update the cell in the cache
    new_key = set_cell_to_cache(new_cell)

    # return the new cell cache key, material name, and parameters
    return (
        {'cache_key': new_key},
        material.name,
        parameter_list, 
        parameter_list, 
        min_values, 
        max_values, 
        marks_list
    )

def handle_property_update(
        triggered_id: dict,
        cell: Type,
        material_type: MaterialType,
        slider_values: List[float],
        input_values: List[float]
) -> Tuple:
    
    # determine the property and subtype from the triggered ID
    property_name = triggered_id['property']

    # get the index of the property in the CC_MATERIAL_PARAMETER_LIST
    property_index = CC_MATERIAL_PARAMETER_LIST.index(property_name)

    # determine the subtype from the triggered ID
    subtype = SubType(triggered_id['subtype'])
    
    # get the value of the new property
    value = slider_values[property_index] if subtype == SubType.SLIDER else input_values[property_index]

    # get the material from the cell
    material = get_material_from_cell(material_type, cell)

    # set the new value to the material
    setattr(material, property_name, value)

    # set the material to the cell
    new_cell = set_material_to_cell(material_type, cell, material)

    # update the cell in the cache
    new_key = set_cell_to_cache(new_cell)

    # calculate new parameters for the material
    parameter_list, min_values, max_values, marks_list = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)
    
    # return the new cell cache key, material name, and parameters
    return (
        {'cache_key': new_key}, 
        material.name, 
        parameter_list, 
        parameter_list, 
        min_values, 
        max_values, 
        marks_list
    )


