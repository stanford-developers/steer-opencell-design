
import time
from dash import callback, Input, Output, State, no_update, ALL, ctx

from App.cache_service import cache

from App.current_collectors.layouts import *
from App.current_collectors.callbacks import CURRENT_COLLECTOR_DESIGNS
from App.current_collectors.callback_helpers import create_generic_current_collector_callback
from App.current_collectors.configs import COLLECTOR_CONFIGS

from App.general.enumerated_classes import CollectorType
from App.general.cell_operations import set_object_to_cell, get_object_from_cell
from App.general.callback_helpers import create_properties_table

from steer_opencell_design.Components.CurrentCollectors import (
    PunchedCurrentCollector,
    NotchedCurrentCollector,
    TablessCurrentCollector,
    TabWeldedCurrentCollector
)



@callback(
    [
        Output('cathode_current_collector_design', 'options'),
        Output('cathode_current_collector_design_div', 'style'),
        Output('cathode_current_collector_design', 'value'),
    ],
    [
        Input('cell_store', 'data'),
    ],
    [
        State('cathode_current_collector_design_div', 'style'),
        State('cathode_current_collector_design', 'options')
    ],
    prevent_initial_call=True
)
def update_cathode_dropdown_options(data, current_style, current_options):
    """
    Update the cathode current collector design dropdown menu options, style, and value
    based on the current collector store data.
    """
    # get the config of the item
    config = COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC]

    # get the cell from the cache
    cell = cache.get(data['cache_key'])

    # get the current collector from the cell
    current_collector = get_object_from_cell(cell, config)

    # Define type mappings
    type_config = {
        PunchedCurrentCollector: {
            'display': 'none',
            'options': [{'label': 'Punched', 'value': 'punched'}],
            'value': 'punched'
        },
        NotchedCurrentCollector: {
            'display': 'block',
            'options': [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched'],
            'value': 'notched'
        },
        TablessCurrentCollector: {
            'display': 'block',
            'options': [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched'],
            'value': 'tabless'
        },
        TabWeldedCurrentCollector: {
            'display': 'block',
            'options': [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched'],
            'value': 'tabbed'
        }
    }

    # Get configuration for current collector type
    collector_type = type(current_collector)

    # get the configuration for the current collector type
    config = type_config.get(collector_type)

    # set the style according to the config display value
    current_style['display'] = config['display']
    
    return config['options'], current_style, config['value']

@callback(
    [
        Output('anode_current_collector_design', 'options'),
        Output('anode_current_collector_design_div', 'style'),
        Output('anode_current_collector_design', 'value'),
    ],
    [
        Input('cell_store', 'data'),
    ],
    [
        State('anode_current_collector_design_div', 'style'),
        State('anode_current_collector_design', 'options')
    ],
    prevent_initial_call=True
)
def update_anode_dropdown_options(data, current_style, current_options):
    """
    Update the anode current collector design dropdown menu options, style, and value
    based on the current collector store data.
    """
    # get the config of the item
    config = COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC]

    # get the cell from the cache
    cell = cache.get(data['cache_key'])

    # get the current collector from the cell
    current_collector = get_object_from_cell(cell, config)

    # Define type mappings
    type_config = {
        PunchedCurrentCollector: {
            'display': 'none',
            'options': [{'label': 'Punched', 'value': 'punched'}],
            'value': 'punched'
        },
        NotchedCurrentCollector: {
            'display': 'block',
            'options': [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched'],
            'value': 'notched'
        },
        TablessCurrentCollector: {
            'display': 'block',
            'options': [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched'],
            'value': 'tabless'
        },
        TabWeldedCurrentCollector: {
            'display': 'block',
            'options': [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched'],
            'value': 'tabbed'
        }
    }

    # Get configuration for current collector type
    collector_type = type(current_collector)

    # get the configuration for the current collector type
    config = type_config.get(collector_type)

    # set the style according to the config display value
    current_style['display'] = config['display']
    
    return config['options'], current_style, config['value']



@callback(
    Output('cell_store', 'data', allow_duplicate=True),
    Input('cathode_current_collector_design', 'value'),
    State('cell_store', 'data'),
    prevent_initial_call=True
)
def update_cathode_current_collector_design(design_value, cell_data):

    """Handle current collector design changes and convert between types."""

    # Check if design_value or cell_data is None
    if not design_value or not cell_data:
        return no_update
    
    # if design_value is punched, return no_update
    if design_value == 'punched':
        return no_update

    # Get current cell and collector
    cell = cache.get(cell_data['cache_key'])

    current_collector = get_object_from_cell(cell, COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC])

    type_name = type(current_collector).__name__

    # Map design values to collector types
    design_to_type = {
        'notched': 'NotchedCurrentCollector', 
        'tabless': 'TablessCurrentCollector',
        'tabbed': 'TabWeldedCurrentCollector'
    }
    
    # get the name of the target collector type
    target_type_name = design_to_type.get(design_value) 

    # If already the correct type, no conversion needed
    if type_name == target_type_name:
        return no_update
    
    # Additional check: If this is likely triggered by cell upload (not user interaction)
    # Check if the current dropdown value already matches the collector type
    current_dropdown_value_map = {
        'NotchedCurrentCollector': 'notched',
        'TablessCurrentCollector': 'tabless', 
        'TabWeldedCurrentCollector': 'tabbed',
        'PunchedCurrentCollector': 'punched'
    }
    
    expected_dropdown_value = current_dropdown_value_map.get(type_name)
    if design_value == expected_dropdown_value:
        # This is likely a cell upload scenario - dropdown was set to match existing collector
        return no_update
    
    # Import function to convert current collector
    from App.current_collectors.callback_helpers import convert_current_collector
    from App.general.cell_operations import set_cell_to_cache

    # Do the conversion
    new_collector = convert_current_collector(current_collector, target_type_name)

    # Assign the new current collector to the cell and get the key
    new_cell = set_object_to_cell(cell, new_collector, COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC])

    # Generate a new cache key
    new_key = set_cell_to_cache(new_cell)

    # Update the dash store with the new cell key
    return {'cache_key': new_key}

@callback(
    Output('cell_store', 'data', allow_duplicate=True),
    Input('anode_current_collector_design', 'value'),
    State('cell_store', 'data'),
    prevent_initial_call=True
)
def update_anode_current_collector_design(design_value, cell_data):
    """Handle current collector design changes and convert between types."""

    # Check if design_value or cell_data is None
    if not design_value or not cell_data:
        return no_update
    
    # if design_value is punched, return no_update
    if design_value == 'punched':
        return no_update

    # Get current cell and collector
    cell = cache.get(cell_data['cache_key'])

    current_collector = get_object_from_cell(cell, COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC])

    type_name = type(current_collector).__name__

    # Map design values to collector types
    design_to_type = {
        'notched': 'NotchedCurrentCollector', 
        'tabless': 'TablessCurrentCollector',
        'tabbed': 'TabWeldedCurrentCollector'
    }
    
    # get the name of the target collector type
    target_type_name = design_to_type.get(design_value) 

    # If already the correct type, no conversion needed
    if type_name == target_type_name:
        return no_update
    
    # Additional check: If this is likely triggered by cell upload (not user interaction)
    # Check if the current dropdown value already matches the collector type
    current_dropdown_value_map = {
        'NotchedCurrentCollector': 'notched',
        'TablessCurrentCollector': 'tabless', 
        'TabWeldedCurrentCollector': 'tabbed',
        'PunchedCurrentCollector': 'punched'
    }
    
    expected_dropdown_value = current_dropdown_value_map.get(type_name)
    if design_value == expected_dropdown_value:
        return no_update
    
    # Import function to convert current collector
    from App.current_collectors.callback_helpers import convert_current_collector
    from App.general.cell_operations import set_cell_to_cache

    # Do the conversion
    new_collector = convert_current_collector(current_collector, target_type_name)

    # Assign the new current collector to the cell and get the key
    new_cell = set_object_to_cell(cell, new_collector, COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC])

    # Generate a new cache key
    new_key = set_cell_to_cache(new_cell)

    # Update the dash store with the new cell key
    return {'cache_key': new_key}



@callback(
    [
        Output('cathode_punched_design_parameters', 'style'),
        Output('cathode_notched_design_parameters', 'style'),
        Output('cathode_tabless_design_parameters', 'style'),
        Output('cathode_tabbed_design_parameters', 'style')
     ],
    Input('cathode_current_collector_design', 'value'),
    prevent_initial_call=True
)
def update_cathode_current_collector_design_parameters(design):
    """
    Update the cathode current collector design parameters based on the current collector store data.
    """
    styles = {'display': 'none'}
    active_style = {'display': 'block'}

    if design is None:
        return [no_update] * 4

    if design == 'punched':
        return [active_style, styles, styles, styles]
    elif design == 'notched':
        return [styles, active_style, styles, styles]
    elif design == 'tabless':
        return [styles, styles, active_style, styles]
    elif design == 'tabbed':
        return [styles, styles, styles, active_style]

@callback(
    [
        Output('anode_punched_design_parameters', 'style'),
        Output('anode_notched_design_parameters', 'style'),
        Output('anode_tabless_design_parameters', 'style'),
        Output('anode_tabbed_design_parameters', 'style')
     ],
    Input('anode_current_collector_design', 'value'),
    prevent_initial_call=True
)
def update_anode_current_collector_design_parameters(design):
    """
    Update the anode current collector design parameters based on the current collector store data.
    """
    styles = {'display': 'none'}
    active_style = {'display': 'block'}

    if design is None:
        return [no_update] * 4

    if design == 'punched':
        return [active_style, styles, styles, styles]
    elif design == 'notched':
        return [styles, active_style, styles, styles]
    elif design == 'tabless':
        return [styles, styles, active_style, styles]
    elif design == 'tabbed':
        return [styles, styles, styles, active_style]



@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    [
        State({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_punched_current_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_values,
    existing_warnings
):

    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_PUNCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
    )

    return response

@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    [
        State({'electrode': 'anode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_anode_punched_current_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_values,
    existing_warnings
):

    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_PUNCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
    )

    return response



@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'step'),

        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),

        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
    ],
    [
        State({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        State({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        State({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_tabless_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings
):

    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_TABLESS)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values
    )
    
    return response

@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'step'),

        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'step'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'step'),
        Output({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),

        Input({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
    ],
    [
        State({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        State({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        State({'electrode': 'anode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_anode_tabless_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings
):

    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_TABLESS)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values
    )
    
    return response



@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'step'),

        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),

        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
    ],
    [
        State({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        State({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        State({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_notched_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings
):

    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_NOTCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values
    )
    
    return response

@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'step'),

        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'step'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'step'),
        Output({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'step'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),

        Input({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
    ],
    [
        State({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        State({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        State({'electrode': 'anode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_anode_notched_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings
):

    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_NOTCHED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values
    )

    return response



@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'step'),

        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'step'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'step'),

        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'radioitem'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'text_input'}, 'value'),
    ],
    [
        Input('cell_store', 'data'),
        
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),

        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_submit'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_blur'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),

        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'radioitem'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'text_input'}, 'value'),
    ],
    [
        State({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        State({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        State({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_cathode_tabbed_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    radioitem_values,
    text_item_values,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings
):

    callback_function = create_generic_current_collector_callback(CollectorType.CATHODE_TABBED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        radioitem_values,
        text_item_values
    )

    return response

@callback(
    [
        Output('warnings_store', 'data', allow_duplicate=True),
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'step'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'step'),

        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'step'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'step'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'step'),

        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'radioitem'}, 'value'),
        Output({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'text_input'}, 'value'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),

        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_submit'),
        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'n_blur'),
        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),

        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'radioitem'}, 'value'),
        Input({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'text_input'}, 'value'),
    ],
    [
        State({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        State({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        State({'electrode': 'anode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        State('warnings_store', 'data'),
    ],
    prevent_initial_call=True
)
def update_anode_tabbed_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_start_n_sub,
    input_start_n_blur,
    input_end_n_sub,
    input_end_n_blur,
    rangeslider_values,
    radioitem_values,
    text_item_values,
    input_values,
    input_start_values,
    input_end_values,
    existing_warnings
):
    print("========")
    print(f'triggered update_anode_tabbed_collector by {ctx.triggered_id} at {time.time()}')
    callback_function = create_generic_current_collector_callback(CollectorType.ANODE_TABBED)

    response = callback_function(
        existing_warnings,
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values,
        radioitem_values,
        text_item_values
    )

    return response



@callback(
    [
        Output('cathode_current_collector_properties_div', 'children'),
    ],
    [
        Input('cell_store', 'data'),
        Input('continue_to_design', 'n_clicks'),
    ],
    prevent_initial_call=True
)
def update_cathode_current_collector_properties(cell_data, continue_to_design):
    """
    Update the cathode current collector plots based on the current collector store data.
    """
    config = COLLECTOR_CONFIGS[CollectorType.CATHODE_GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    current_collector = get_object_from_cell(cell, config)

    # get the current collector properties
    properties = current_collector.properties

    # Create properties table using utility function
    properties_table = create_properties_table(properties, table_id='cathode_current_collector_properties_table', decimal_places=2)

    # return the plots
    return [properties_table]

@callback(
    [
        Output('anode_current_collector_properties_div', 'children'),
    ],
    [
        Input('cell_store', 'data'),
        Input('continue_to_design', 'n_clicks'),
    ],
    prevent_initial_call=True
)
def update_anode_current_collector_properties(cell_data, continue_to_design):
    """
    Update the anode current collector plots based on the current collector store data.
    """
    config = COLLECTOR_CONFIGS[CollectorType.ANODE_GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    current_collector = get_object_from_cell(cell, config)

    # get the current collector properties
    properties = current_collector.properties

    # Create properties table using utility function
    properties_table = create_properties_table(properties, table_id='anode_current_collector_properties_table', decimal_places=2)

    # return the plots
    return [properties_table]





