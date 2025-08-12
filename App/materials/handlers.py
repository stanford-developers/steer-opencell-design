from typing import Type, Tuple, List
from dash import no_update

from current_collectors.lists import CC_MATERIAL_PARAMETER_LIST
from materials.callback_helpers import create_no_update_response
from materials.cell_operations import get_material_from_cell, set_material_to_cell
from general.enumerated_classes import MaterialType, SubType
from general.callback_helpers import generate_parameters
from general.cell_operations import set_cell_to_cache
from steer_opencell_design.Components.CurrentCollectors import CurrentCollectorMaterial

from steer_core.Apps.Utils.SliderControls import create_slider_config, are_slider_input_values_incompatible


def handle_cell_store_update(
    cell: Type,
    material_type: MaterialType
) -> Tuple:
    
    # get the material from the cell
    material = get_material_from_cell(material_type, cell)

    # If material doesn't exist (e.g., tab material on non-tabbed collector), return no_update
    if material is None:
        return create_no_update_response()

    # get the parameters for the material
    parameter_list, min_values, max_values = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)

    # get the slider configurations
    slider_configs = create_slider_config(min_values, max_values, parameter_list)
    min_values = slider_configs['min_vals']
    max_values = slider_configs['max_vals']
    step_values = slider_configs['step_vals']
    mark_values = slider_configs['mark_vals']
    slider_values = slider_configs['grid_slider_vals']
    input_values = slider_configs['grid_input_vals']
    input_steps = slider_configs['input_step_vals']

    # return the no_update response with the material name and parameters
    return (
        no_update, 
        material.name, 
        slider_values, 
        min_values, 
        max_values, 
        mark_values, 
        step_values, 
        input_values, 
        input_steps
    )


def handle_selector_update(
    material_name: str,
    cell: Type,
    material_type: MaterialType
) -> Tuple:
    """
    Handle updates to the material selector.

    Parameters
    ----------s
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
    parameter_list, min_values, max_values = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)

    # get the slider configurations
    slider_configs = create_slider_config(min_values, max_values, parameter_list)
    min_values = slider_configs['min_vals']
    max_values = slider_configs['max_vals']
    step_values = slider_configs['step_vals']
    mark_values = slider_configs['mark_vals']
    slider_values = slider_configs['grid_vals']
    input_steps = slider_configs['input_step_vals']

    # set the material to the cell
    new_cell = set_material_to_cell(material_type, cell, material)
    
    # update the cell in the cache
    new_key = set_cell_to_cache(new_cell)

    # return the new cell cache key, material name, and parameters
    return (
        {'cache_key': new_key},
        material.name,
        slider_values,
        min_values,
        max_values,
        mark_values,
        step_values,
        parameter_list,
        input_steps
    )


def handle_drag_value_update(
        triggered_id: dict, 
        drag_values: List[float], 
        slider_steps: List[float], 
        input_steps: List[float], 
        input_values: List[float]
    ) -> Tuple:
    """
    Handle updates to the drag value of a slider.

    Parameters
    ----------
    triggered_id : dict
        The ID of the component that triggered the event.
    drag_values : List[float]
        The current values of the sliders being dragged.

    Returns
    -------
    Tuple
        A tuple containing the updated values for the affected components.
    """
    # get the name of the property that triggered the event
    property_name = triggered_id['property']

    # get the index of the property in the CC_MATERIAL_PARAMETER_LIST
    property_index = CC_MATERIAL_PARAMETER_LIST.index(property_name)

    drag_value = drag_values[property_index]
    slider_step = slider_steps[property_index]
    input_step = input_steps[property_index]
    input_value = input_values[property_index]

    # create a no response
    default_response = create_no_update_response()

    if are_slider_input_values_incompatible(drag_value, input_value, slider_step, input_step):
        default_response[-2][property_index] = drag_values[property_index]

    return default_response


def handle_property_update(
        triggered_id: dict,
        cell: Type,
        material_type: MaterialType,
        input_values: List[str],
        slider_values: List[float]
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
    parameter_list, min_values, max_values = generate_parameters(material, CC_MATERIAL_PARAMETER_LIST)
    
    # get the slider configurations
    slider_configs = create_slider_config(min_values, max_values, parameter_list)
    slider_vals = slider_configs['grid_slider_vals']
    input_vals = slider_configs['grid_input_vals']
    min_values = slider_configs['min_vals']
    max_values = slider_configs['max_vals']
    step_values = slider_configs['step_vals']
    mark_values = slider_configs['mark_vals']
    input_steps = slider_configs['input_step_vals']

    # return the new cell cache key, material name, and parameters
    return (
        {'cache_key': new_key}, 
        material.name, 
        slider_vals, 
        min_values, 
        max_values,
        mark_values,
        step_values,
        input_vals,
        input_steps
    )


