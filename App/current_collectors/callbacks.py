from dash import callback, Input, Output, ctx, State, no_update, MATCH, ALL, dash_table, clientside_callback

from cache_service import cache

from steer_opencell_design.Components.CurrentCollectors import *

from current_collectors.layouts import *
from current_collectors.callbacks import CURRENT_COLLECTOR_DESIGNS
from current_collectors.callback_helpers import create_generic_current_collector_callback
from current_collectors.configs import COLLECTOR_CONFIGS

from general.enumerated_classes import CollectorType, ElectrodeType
from general.cell_operations import set_object_to_cell, get_object_from_cell


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
    config = COLLECTOR_CONFIGS[CollectorType.GENERIC]

    # get the cell from the cache
    cell = cache.get(data['cache_key'])

    # get the current collector from the cell
    current_collector = get_object_from_cell(cell, config)

    # If the current collector is None, return no_update
    if current_collector is None:
        return current_options, current_style, no_update

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
def update_current_collector_design(design_value, cell_data):
    """Handle current collector design changes and convert between types."""
    
    # Check if design_value or cell_data is None
    if not design_value or not cell_data:
        return no_update
    
    # if design_value is punched, return no_update
    if design_value == 'punched':
        return no_update

    # Get current cell and collector
    cell = cache.get(cell_data['cache_key'])

    current_collector = get_object_from_cell(cell, COLLECTOR_CONFIGS[CollectorType.GENERIC])

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
    from current_collectors.callback_helpers import convert_current_collector
    from general.callback_helpers import set_cell_to_cache

    # Do the conversion
    new_collector = convert_current_collector(current_collector, target_type_name)

    # Assign the new current collector to the cell and get the key
    new_cell = set_object_to_cell(cell, new_collector)

    # Generate a new cache key
    new_key = set_cell_to_cache(new_cell)

    # Update the dash store with the new cell key
    return {'cache_key': new_key}


# @callback(
#     [
#         Output('cell_store', 'data', allow_duplicate=True),
#         Output('cathode_current_collector_tab_material_selector', 'value'),
#         Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'marks'),
#     ],
#     [
#         Input('cell_store', 'data'),
#         Input('cathode_current_collector_tab_material_selector', 'value'),
#         Input({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'value'),
#     ],
#     prevent_initial_call=True
# )
# def update_cathode_current_collector_tab_material(
#     cell_data,
#     material_selector,
#     input_values,
#     slider_values
# ):
    
#     callback_function = create_material_callback(MaterialType.CATHODE_CURRENT_COLLECTOR_TAB)

#     response = callback_function(
#         cell_data,
#         material_selector,
#         input_values,
#         slider_values
#     )

#     return response


@callback(
    [Output('cathode_punched_design_parameters', 'style'),
     Output('cathode_notched_design_parameters', 'style'),
     Output('cathode_tabless_design_parameters', 'style'),
     Output('cathode_tabbed_design_parameters', 'style')],
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
    ],
    prevent_initial_call=True
)
def update_punched_current_collector(
    cell_data,
    input_n_sub,
    input_n_blur,
    slider_values,
    input_values,
):

    callback_function = create_generic_current_collector_callback(
        CollectorType.PUNCHED,
        ElectrodeType.CATHODE
    )

    response = callback_function(
        cell_data,
        input_values,
        slider_values,
    )

    response = response

    return response


@callback(
    [
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
    ],
    prevent_initial_call=True
)
def update_tabless_collector(
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
    input_end_values
):

    callback_function = create_generic_current_collector_callback(
        CollectorType.TABLESS,
        ElectrodeType.CATHODE
    )

    response = callback_function(
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values
    )

    response = response

    return response




@callback(
    [
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
    ],
    prevent_initial_call=True
)
def update_notched_collector(
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
    input_end_values
):

    callback_function = create_generic_current_collector_callback(
        CollectorType.NOTCHED,
        ElectrodeType.CATHODE
    )

    response = callback_function(
        cell_data,
        input_values,
        slider_values,
        rangeslider_values,
        input_start_values,
        input_end_values
    )

    response = response

    return response




# @callback(
#     [
#         Output('cell_store', 'data', allow_duplicate=True),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
#     ],
#     [
#         Input('cell_store', 'data'),
#         Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'action': 'flip_x'}, 'n_clicks'),
#         Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'action': 'flip_y'}, 'n_clicks'),
#         # Add range slider inputs
#         Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
#     ],
#     prevent_initial_call=True
# )
# def update_notched_current_collector(cell_data, input_values, slider_values, flip_x, flip_y, rangeslider_values, input_start_values, input_end_values):

#     callback_function = create_generic_current_collector_callback(
#         CollectorType.NOTCHED,
#         ElectrodeType.CATHODE
#     )

#     response = callback_function(
#         cell_data,
#         input_values,
#         slider_values,
#         flip_x,
#         flip_y,
#         rangeslider_values,
#         input_start_values,
#         input_end_values
#     )

#     return response



# @callback(
#     [
#         Output('cell_store', 'data', allow_duplicate=True),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': 'tab_weld_side', 'subtype': 'radioitem'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': 'weld_tab_positions', 'subtype': 'text_input'}, 'value'),
#     ],
#     [
#         Input('cell_store', 'data'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'action': 'flip_x'}, 'n_clicks'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'action': 'flip_y'}, 'n_clicks'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': 'tab_weld_side', 'subtype': 'radioitem'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': 'weld_tab_positions', 'subtype': 'text_input'}, 'value'),
#     ],
#     prevent_initial_call=True
# )
# def update_tabbed_current_collector(
#     cell_data, input_values, slider_values, flip_x, flip_y, 
#     rangeslider_values, input_start_values, input_end_values, 
#     tab_weld_side, tab_positions_text
# ):

#     callback_function = create_generic_current_collector_callback(
#         CollectorType.TABBED,
#         ElectrodeType.CATHODE
#     )

#     response = callback_function(
#         cell_data,
#         input_values,
#         slider_values,
#         flip_x,
#         flip_y,
#         rangeslider_values,
#         input_start_values,
#         input_end_values,
#         tab_weld_side,
#         tab_positions_text
#     )

#     return response


@callback(
    [
        Output('cathode_current_collector_a_side_plot', 'figure'),
        Output('cathode_current_collector_properties_table', 'children'),
    ],
    [
        Input('cell_store', 'data'),
        Input('continue_to_design', 'n_clicks'),
    ],
    prevent_initial_call=True
)
def update_cathode_current_collector_plots(cell_data, continue_to_design):
    """
    Update the cathode current collector plots based on the current collector store data.
    """
    config =  COLLECTOR_CONFIGS[CollectorType.GENERIC]

    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    current_collector = get_object_from_cell(cell, config)

    # get the plots from the current collector
    a_side_plot = current_collector.get_a_side_view(with_dimensions=False, title='A-Side Current Collector View')

    # get the current collector properties
    properties = current_collector.properties

    # get the current collector properties
    properties = current_collector.properties

    # Create properties table from dictionary
    if properties and isinstance(properties, dict):
        # Convert dictionary to list of records for DataTable
        table_data = []
        for key, value in properties.items():
            # Format the property name (replace underscores, capitalize)
            formatted_key = key.replace('_', ' ').title()
            
            # Format the value based on type
            if isinstance(value, float):
                formatted_value = f"{value:.4f}"
            elif isinstance(value, int):
                formatted_value = str(value)
            else:
                formatted_value = str(value)
            
            table_data.append({
                'Property': formatted_key,
                'Value': formatted_value
            })
        
        properties_table = dash_table.DataTable(
            data=table_data,
            columns=[
                {"name": "Property", "id": "Property"},
                {"name": "Value", "id": "Value"}
            ],
            style_table={
                'overflowX': 'auto',
                'border': '1px solid #ddd',
                'borderRadius': '5px'
            },
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'border': '1px solid #ddd',
                'fontFamily': 'Arial, sans-serif'
            },
            style_header={
                'backgroundColor': '#f8f9fa',
                'fontWeight': 'bold',
                'border': '1px solid #ddd'
            },
            style_data={
                'backgroundColor': '#ffffff',
            }
        )
    else:
        # Fallback if no properties available
        properties_table = ds.html.Div([
            ds.html.P("No properties available", 
                     style={'textAlign': 'center', 'color': '#666', 'fontStyle': 'italic'})
        ])

    # return the plots
    return a_side_plot, properties_table

