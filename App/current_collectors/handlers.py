from typing import Type, Tuple, List

from dash import no_update

from general.enumerated_classes import SubType
from general.callback_helpers import generate_parameters
from general.cell_operations import set_cell_to_cache, set_object_to_cell
from general.enumerated_classes import ActionType
from general.callback_helpers import generate_rangeslider_values


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
    new_cell = set_object_to_cell(cell, current_collector)
    
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
    from current_collectors.callback_helpers import format_tab_positions
    tab_positions = getattr(current_collector, 'tab_positions', [])
    response.append(format_tab_positions(tab_positions))
    
    return tuple(response)





