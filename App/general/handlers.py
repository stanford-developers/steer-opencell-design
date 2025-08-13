from dash import no_update
from typing import Type, Tuple, List, Any
import time

from general.enumerated_classes import SubType, TriggerType
from general.cell_operations import set_cell_to_cache, set_object_to_cell
from general.callback_helpers import (
    validate_dependent_properties, 
    generate_parameters, 
    generate_rangeslider_values, 
    validate_single_property
)

from steer_core.Apps.Utils.SliderControls import create_slider_config, create_range_slider_config


def _build_basic_response(slider_configs: dict, cache_key: str = None) -> List[Any]:
    """Build the basic response components from slider configurations."""

    dict_key = {'cache_key': cache_key}
    
    return [
        dict_key if cache_key is not None else no_update,
        slider_configs['grid_slider_vals'],
        slider_configs['min_vals'],
        slider_configs['max_vals'],
        slider_configs['mark_vals'],
        slider_configs['step_vals'],
        slider_configs['input_step_vals']
    ]


def _add_dropdown_menu(response: List[Any], object_instance: Type, config: Type) -> None:
    """Add dropdown menu value if applicable."""
    if hasattr(config, 'dropdown_menu') and config.dropdown_menu:
        response.append(object_instance.name)


def _add_range_slider_components(response: List[Any], object_instance: Type, config: Type) -> None:
    """Add range slider components if applicable."""
    if not (hasattr(config, 'range_slider_parameters') and config.range_slider_parameters):
        return
    
    # Generate range slider values
    start_values, end_values, min_values, max_values = generate_rangeslider_values(object_instance, config.range_slider_parameters)
    
    # Create range slider configurations
    range_slider_configs = create_range_slider_config(min_values, max_values, start_values, end_values)
    
    # Add all range slider components to response
    response.extend([
        range_slider_configs['grid_slider_vals'],
        range_slider_configs['min_vals'],
        range_slider_configs['max_vals'],
        range_slider_configs['mark_vals'],
        range_slider_configs['step_vals'],
        range_slider_configs['input_step_vals'],
        range_slider_configs['input_step_vals'],
    ])


def _add_tabbed_collector_components(response: List[Any], object_instance: Type, config: Type) -> None:
    """Add tab weld side and position components for tabbed collectors."""
    is_tabbed_collector = (
        hasattr(config, 'collector_type') and 
        config.collector_type.__name__ == 'TabWeldedCurrentCollector'
    )
    
    if not is_tabbed_collector:
        return
    
    # Add tab weld side
    response.append(object_instance.tab_weld_side)
    
    # Add formatted tab positions
    from current_collectors.callback_helpers import format_tab_positions
    tab_positions = getattr(object_instance, 'weld_tab_positions', [])
    formatted_text = format_tab_positions(tab_positions)
    response.append(formatted_text)


def handle_cell_store_update(object_instance: Type, config: Type) -> Tuple:
    """
    Handle cell store update for any collector type.
    
    Args:
        object_instance: The collector object instance
        config: Configuration object containing parameters and settings
        
    Returns:
        Tuple containing all the UI component values for the callback
        
    Raises:
        AttributeError: If required attributes are missing from config or object
    """
    # Validate all dependent properties first
    validate_dependent_properties(object_instance, config)
    
    # Generate basic parameters
    parameter_list, min_values, max_values = generate_parameters(object_instance, config)
    
    # Create slider configurations
    slider_configs = create_slider_config(min_values, max_values, parameter_list)
    
    # Build the base response
    response = _build_basic_response(slider_configs)
    
    # Add optional components based on configuration
    _add_dropdown_menu(response, object_instance, config)
    _add_range_slider_components(response, object_instance, config)
    _add_tabbed_collector_components(response, object_instance, config)
    
    return tuple(response)


def handle_property_update(
        triggered_id: dict,
        cell: Type, 
        object_instance: Type,
        config: Type,
        input_values: List[float],
        slider_values: List[float],
        range_slider_values: List[float] = None,
        input_start_values: List[float] = None,
        input_end_values: List[float] = None
    ) -> Tuple:

    # determine the property and subtype from the triggered ID
    property_name = triggered_id['property']

    # determine the subtype from the triggered ID
    subtype = SubType(triggered_id['subtype'])

    # Determine the value from the input type
    if subtype == SubType.INPUT:
        property_index = config.settable_parameters.index(property_name)
        value = input_values[property_index]
    elif subtype == SubType.SLIDER:
        property_index = config.settable_parameters.index(property_name)
        value = slider_values[property_index]
    elif subtype == SubType.RANGESLIDER:
        property_index = config.range_slider_parameters.index(property_name)
        value = range_slider_values[property_index]
    elif subtype == SubType.INPUT_START:
        property_index = config.range_slider_parameters.index(property_name)
        value = range_slider_values[property_index]
        value[0] = input_start_values[property_index]
    elif subtype == SubType.INPUT_END:
        property_index = config.range_slider_parameters.index(property_name)
        value = range_slider_values[property_index]
        value[1] = input_end_values[property_index]

    # Do a pre check to make sure the value is in an appropriate range
    value = validate_single_property(object_instance, property_name, value, config)

    # set the new value to the object instance
    setattr(object_instance, property_name, value)

    # validate all dependent properties first
    validate_dependent_properties(object_instance, config)

    # make new cell
    new_cell = set_object_to_cell(cell, object_instance, config)

    # get the new key
    new_key = set_cell_to_cache(new_cell)

    # get the new parameters
    parameter_list, min_values, max_values = generate_parameters(object_instance, config)

    # Create slider configurations
    slider_configs = create_slider_config(min_values, max_values, parameter_list)

    # Build the base response
    response = _build_basic_response(slider_configs, new_key)

    # Add optional components based on configuration
    _add_dropdown_menu(response, object_instance, config)
    _add_range_slider_components(response, object_instance, config)
    _add_tabbed_collector_components(response, object_instance, config)

    return tuple(response)




# def handle_property_update(
#     triggered_id: dict,
#     current_collector,
#     config: Type,
#     cell: Type,
#     input_values: list,
#     slider_values: list,
#     rangeslider_values: list = None,
#     input_start_values: list = None,
#     input_end_values: list = None,
#     tab_positions_text: str = None  # Add this parameter
# ) -> Tuple:
#     """Handle property updates for any collector type."""
    
#     property_name = triggered_id['property']
#     subtype = SubType(triggered_id['subtype']) 

#     # Handle text input for tab positions
#     if subtype == SubType.TEXT_INPUT and property_name == 'weld_tab_positions':
#         from current_collectors.callback_helpers import parse_tab_positions
#         positions = parse_tab_positions(tab_positions_text)
#         setattr(current_collector, property_name, positions)
    
#     # Handle range slider properties
#     elif config.range_slider_parameters and property_name in config.range_slider_parameters:

#         range_property_index = config.range_slider_parameters.index(property_name)
        
#         if subtype == SubType.RANGESLIDER:
#             value = rangeslider_values[range_property_index]
#         elif subtype == SubType.INPUT_START:
#             current_value = getattr(current_collector, property_name)
#             value = (input_start_values[range_property_index], current_value[1])
#         elif subtype == SubType.INPUT_END:
#             current_value = getattr(current_collector, property_name)
#             value = (current_value[0], input_end_values[range_property_index])
        
#         setattr(current_collector, property_name, value)
    
#     # Handle regular slider/input properties
#     elif property_name in config.parameter_list:
#         property_index = config.parameter_list.index(property_name)
#         if subtype == SubType.SLIDER:
#             value = slider_values[property_index]
#         elif subtype == SubType.INPUT:
#             value = input_values[property_index]
#         setattr(current_collector, property_name, value)
    
#     # Validate dependent properties
#     validate_dependent_properties(current_collector, config.settable_parameters)
    
#     # Generate updated parameters
#     from general.callback_helpers import generate_parameters
#     value_list, min_values, max_values = generate_parameters(current_collector, config.parameter_list)
    
#     # get the slider configurations
#     slider_configs = create_slider_config(min_values, max_values, value_list)
#     min_values = slider_configs['min_vals']
#     max_values = slider_configs['max_vals']
#     step_values = slider_configs['step_vals']
#     mark_values = slider_configs['mark_vals']
#     input_steps = slider_configs['input_step_vals']
#     slider_vals = slider_configs['grid_slider_vals']
#     input_vals = slider_configs['grid_input_vals']

#     # Update cell
#     new_cell = set_current_collector_to_cell(cell, current_collector)
    
#     # Update cache
#     new_key = set_cell_to_cache(new_cell)

#     # Build response
#     response = [
#         {'cache_key': new_key},
#         slider_vals,
#         min_values,
#         max_values,
#         mark_values,
#         step_values,
#         input_vals,
#         input_steps
#     ]
    
#     # Add range slider values if applicable
#     if config.range_slider_parameters:
#         start_values, end_values, min_values, max_values = generate_rangeslider_values(current_collector, config.range_slider_parameters)
#         range_slider_configs = create_range_slider_config(min_values, max_values, start_values, end_values)
#         range_slider_values = range_slider_configs['grid_slider_vals']
#         input_start_values = [v[0] for v in range_slider_configs['grid_input_vals']]
#         input_end_values = [v[1] for v in range_slider_configs['grid_input_vals']]
#         range_slider_minimum_values = range_slider_configs['min_vals']
#         range_slider_maximum_values = range_slider_configs['max_vals']
#         range_slider_marks = range_slider_configs['mark_vals']
#         range_slider_step_values = range_slider_configs['step_vals']

#         response.append(range_slider_values)
#         response.append(input_start_values)
#         response.append(input_end_values)
#         response.append(range_slider_minimum_values)
#         response.append(range_slider_maximum_values)
#         response.append(range_slider_marks)
#         response.append(range_slider_step_values)

#     # Add the current tab_weld_side value AND text input (ONLY for tabbed collectors)
#     if config.collector_type.__name__ == 'TabWeldedCurrentCollector':
#         response.append(current_collector.tab_weld_side)
        
#         # Add formatted tab positions text
#         from current_collectors.callback_helpers import format_tab_positions
#         tab_positions = getattr(current_collector, 'weld_tab_positions', [])
#         response.append(format_tab_positions(tab_positions))
    
#     return tuple(response)