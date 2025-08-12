from typing import Type, Tuple, List

from dash import no_update

from general.enumerated_classes import SubType
from general.callback_helpers import validate_dependent_properties, generate_parameters
from general.cell_operations import set_cell_to_cache
from general.enumerated_classes import ActionType
from general.callback_helpers import generate_rangeslider_values

from current_collectors.cell_operations import set_current_collector_to_cell

from steer_core.Apps.Utils.SliderControls import create_slider_config, are_slider_input_values_incompatible


def handle_drag_value_update(
        triggered_id: dict, 
        drag_values: List[float], 
        config: Type, 
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
    property_index = config.parameter_list.index(property_name)

    # create a no response
    from current_collectors.callback_helpers import create_no_update_response
    default_response = create_no_update_response(config)

    drag_value = drag_values[property_index]
    slider_step = slider_steps[property_index]
    input_step = input_steps[property_index]
    input_value = input_values[property_index]

    if are_slider_input_values_incompatible(drag_value, input_value, slider_step, input_step):
        default_response[-2][property_index] = drag_values[property_index]

    return default_response


def handle_cell_store_update(object: Type, config: Type) -> Tuple:
    """Handle cell store update for any collector type."""
    
    # IMPORTANT: Validate all dependent properties first
    validate_dependent_properties(
        object,
        config.settable_parameters, 
        None
    )
    
    # Generate basic parameters
    parameter_list, min_values, max_values = generate_parameters(object, config.parameter_list)
    
    # get the slider configurations
    slider_configs = create_slider_config(min_values, max_values, parameter_list)
    min_values = slider_configs['min_vals']
    max_values = slider_configs['max_vals']
    step_values = slider_configs['step_vals']
    mark_values = slider_configs['mark_vals']
    input_steps = slider_configs['input_step_vals']
    slider_vals = slider_configs['grid_slider_vals']
    input_vals = slider_configs['grid_input_vals']

    # Start building response
    response = [
        no_update,  # cache_key stays the same
        slider_vals,
        min_values,
        max_values,
        mark_values,
        step_values,
        input_vals,
        input_steps
    ]
    
    # Add range slider values if applicable
    if config.range_slider_parameters:
        range_values, start_list, end_list, min_val, max_val, range_marks = generate_rangeslider_values(
            object, config.range_slider_parameters
        )
        response.extend([range_values, start_list, end_list, min_val, max_val, range_marks])
    
    # Add the current tab_weld_side value AND text input (ONLY for tabbed collectors)
    if config.collector_type.__name__ == 'TabWeldedCurrentCollector':
        response.append(object.tab_weld_side)

        # Use consistent property name
        tab_positions = getattr(object, 'weld_tab_positions', [])
        formatted_text = format_tab_positions(tab_positions)
        response.append(formatted_text)
    
    return tuple(response)

def handle_property_update(
    triggered_id: dict,
    current_collector,
    config: Type,
    cell: Type,
    input_values: list,
    slider_values: list,
    rangeslider_values: list = None,
    input_start_values: list = None,
    input_end_values: list = None,
    tab_positions_text: str = None  # Add this parameter
) -> Tuple:
    """Handle property updates for any collector type."""
    
    property_name = triggered_id['property']
    subtype = SubType(triggered_id['subtype']) 

    # Handle text input for tab positions
    if subtype == SubType.TEXT_INPUT and property_name == 'weld_tab_positions':
        positions = parse_tab_positions(tab_positions_text)
        setattr(current_collector, property_name, positions)
    
    # Handle range slider properties
    elif config.range_slider_parameters and property_name in config.range_slider_parameters:

        range_property_index = config.range_slider_parameters.index(property_name)
        
        if subtype == SubType.RANGESLIDER:
            value = rangeslider_values[range_property_index]
        elif subtype == SubType.INPUT_START:
            current_value = getattr(current_collector, property_name)
            value = (input_start_values[range_property_index], current_value[1])
        elif subtype == SubType.INPUT_END:
            current_value = getattr(current_collector, property_name)
            value = (current_value[0], input_end_values[range_property_index])
        
        setattr(current_collector, property_name, value)
    
    # Handle regular slider/input properties
    elif property_name in config.parameter_list:
        property_index = config.parameter_list.index(property_name)
        if subtype == SubType.SLIDER:
            value = slider_values[property_index]
        elif subtype == SubType.INPUT:
            value = input_values[property_index]
        setattr(current_collector, property_name, value)
    
    # Validate dependent properties
    validate_dependent_properties(current_collector, config.settable_parameters, property_name)
    
    # Generate updated parameters
    from general.callback_helpers import generate_parameters
    value_list, min_values, max_values = generate_parameters(current_collector, config.parameter_list)
    
    # get the slider configurations
    slider_configs = create_slider_config(min_values, max_values, value_list)
    min_values = slider_configs['min_vals']
    max_values = slider_configs['max_vals']
    step_values = slider_configs['step_vals']
    mark_values = slider_configs['mark_vals']
    input_steps = slider_configs['input_step_vals']
    slider_vals = slider_configs['grid_slider_vals']
    input_vals = slider_configs['grid_input_vals']

    # Update cell
    new_cell = set_current_collector_to_cell(cell, current_collector)
    
    # Update cache
    new_key = set_cell_to_cache(new_cell)

    # Build response
    response = [
        {'cache_key': new_key},
        slider_vals,
        min_values,
        max_values,
        mark_values,
        step_values,
        input_vals,
        input_steps
    ]
    
    # Add range slider values if applicable
    if config.range_slider_parameters:
        range_values, start_list, end_list, min_val, max_val, range_marks = generate_rangeslider_values(
            current_collector, config.range_slider_parameters
        )
        response.extend([range_values, start_list, end_list, min_val, max_val, range_marks])
    
    # Add the current tab_weld_side value AND text input (ONLY for tabbed collectors)
    if config.collector_type.__name__ == 'TabWeldedCurrentCollector':
        response.append(current_collector.tab_weld_side)
        
        # Add formatted tab positions text
        tab_positions = getattr(current_collector, 'weld_tab_positions', [])
        response.append(format_tab_positions(tab_positions))
    
    return tuple(response)

def handle_action(
    triggered_id: dict,
    current_collector,
    config: Type,
    cell: dict
) -> Tuple:
    """Handle flip actions for any collector type."""
    
    action = ActionType(triggered_id['action']) 

    # Perform the flip using enum
    if action == ActionType.FLIP_X:
        current_collector.flip(axis='x')
    elif action == ActionType.FLIP_Y:
        current_collector.flip(axis='y')
    elif action == ActionType.ROTATE:
        current_collector.rotate_90()

    # Update cache
    new_cell = set_current_collector_to_cell(cell, current_collector)
    
    # update the cell in the cache
    new_key = set_cell_to_cache(new_cell)

    # Create the standard no_update response but replace the cache_key
    from current_collectors.callback_helpers import create_no_update_response
    response = list(create_no_update_response(config))
    response[0] = {'cache_key': new_key}  # Replace the first element (cache_key)

    return tuple(response)

def handle_side_selector_update(
    triggered_id: dict,
    current_collector,
    config: Type,
    cell: Type,
    tab_weld_side: str
) -> Tuple:
    """Handle side selector (RadioItems) updates."""
    
    property_name = triggered_id['property']
    
    if property_name == 'tab_weld_side':
        setattr(current_collector, property_name, tab_weld_side)
    
    # update cell
    new_cell = set_current_collector_to_cell(cell, current_collector)
    
    # update the cell in the cache
    new_key = set_cell_to_cache(new_cell)

    # Generate updated parameters
    value_list, min_values, max_values, marks_list = generate_parameters(current_collector, config.parameter_list)

    # Build response
    response = [
        {'cache_key': new_key},
        value_list,
        value_list,
        min_values,
        max_values,
        min_values,
        max_values,
        marks_list,
    ]
    
    # Add range slider values if applicable
    if config.range_slider_parameters:
        range_values, start_list, end_list, min_val, max_val, range_marks = generate_rangeslider_values(
            current_collector, config.range_slider_parameters
        )
        response.extend([range_values, start_list, end_list, min_val, max_val, range_marks])
    
    # Add the current tab_weld_side value AND text input
    response.append(current_collector.tab_weld_side)
    
    # Add formatted tab positions text
    tab_positions = getattr(current_collector, 'tab_positions', [])
    response.append(format_tab_positions(tab_positions))
    
    return tuple(response)

def parse_tab_positions(text_input: str) -> List[float]:
    """Parse comma-separated tab positions from text input."""
    if not text_input or not text_input.strip():
        return []
    
    try:
        # Split by comma and clean up whitespace
        positions = [x.strip() for x in text_input.split(',') if x.strip()]
        # Convert to float and filter out invalid values
        positions = [float(x) for x in positions if x.replace('.', '').replace('-', '').isdigit()]
        # Sort positions and remove duplicates
        positions = sorted(list(set(positions)))
        return positions
    except (ValueError, AttributeError):
        return []  # Return empty list if parsing fails
    
def format_tab_positions(positions: List[float]) -> str:
    """Format list of positions as comma-separated string."""
    if not positions:
        return ''
    return ', '.join([str(pos) for pos in sorted(positions)])


