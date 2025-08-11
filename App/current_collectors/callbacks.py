from dash import callback, Input, Output, ctx, State, no_update, MATCH, ALL, clientside_callback

from cache_service import cache

from steer_opencell_design.Components.CurrentCollectors import *

from current_collectors.layouts import *
from current_collectors.callbacks import CURRENT_COLLECTOR_DESIGNS
from current_collectors.callback_helpers import create_generic_current_collector_callback
from general.callback_helpers import create_material_callback
from current_collectors.cell_operations import get_current_collector_from_cell, set_current_collector_to_cell
from general.enumerated_classes import CollectorType, ElectrodeType, MaterialType


clientside_callback(
    "window.dash_clientside.slider_sync.sync_drag_to_input",
    Output({'electrode': 'cathode', 'object': 'material', 'property': MATCH, 'subtype': 'input'}, 'value'),
    Input({'electrode': 'cathode', 'object': 'material', 'property': MATCH, 'subtype': 'slider'}, 'drag_value'),
    prevent_initial_call=True
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
    # get the cell from the cache
    cell = cache.get(data['cache_key'])

    # get the current collector from the cell
    current_collector = get_current_collector_from_cell(cell, ElectrodeType.CATHODE)

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
    current_collector = get_current_collector_from_cell(cell, ElectrodeType.CATHODE)

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
    
    # Import function to convert current collector
    from current_collectors.callback_helpers import convert_current_collector
    from general.callback_helpers import set_cell_to_cache

    # Do the conversion
    new_collector = convert_current_collector(current_collector, target_type_name)

    # Assign the new current collector to the cell and get the key
    new_cell = set_current_collector_to_cell(cell, new_collector)

    # Generate a new cache key
    new_key = set_cell_to_cache(new_cell)

    # Update the dash store with the new cell key
    return {'cache_key': new_key}


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode_current_collector_material_selector', 'value'),
        # Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'marks'),
    ],
    [
        Input('cell_store', 'data'),
        Input('cathode_current_collector_material_selector', 'value'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    prevent_initial_call=True
)
def update_cathode_current_collector_material(
    cell_data,
    material_selector,
    input_values,
    slider_values,
):
    
    callback_function = create_material_callback(MaterialType.CATHODE_CURRENT_COLLECTOR)

    response = callback_function(
        cell_data,
        material_selector,
        input_values,
        slider_values
    )

    response_list = list(response)
    response = response_list[:2] + response_list[3:]
    response = tuple(response)

    return response


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


# @callback(
#     [Output('cathode_punched_design_parameters', 'style'),
#      Output('cathode_notched_design_parameters', 'style'),
#      Output('cathode_tabless_design_parameters', 'style'),
#      Output('cathode_tabbed_design_parameters', 'style')],
#     Input('cathode_current_collector_design', 'value'),
#     prevent_initial_call=True
# )
# def update_cathode_current_collector_design_parameters(design):
#     """
#     Update the cathode current collector design parameters based on the current collector store data.
#     """
#     styles = {'display': 'none'}
#     active_style = {'display': 'block'}

#     if design is None:
#         return [no_update] * 4

#     if design == 'punched':
#         return [active_style, styles, styles, styles]
#     elif design == 'notched':
#         return [styles, active_style, styles, styles]
#     elif design == 'tabless':
#         return [styles, styles, active_style, styles]
#     elif design == 'tabbed':
#         return [styles, styles, styles, active_style]


# @callback(
#     [
#         Output('cell_store', 'data', allow_duplicate=True),
#         Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks')
#     ],
#     [
#         Input('cell_store', 'data'),
#         Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'action': 'flip_x'}, 'n_clicks'),
#         Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'action': 'flip_y'}, 'n_clicks'),
#         Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'action': 'rotate'}, 'n_clicks')
#     ],
#     prevent_initial_call=True
# )
# def update_punched_current_collector(cell_data, input_values, slider_values, flip_x, flip_y, rotate):

#     callback_function = create_generic_current_collector_callback(
#         CollectorType.PUNCHED,
#         ElectrodeType.CATHODE
#     )

#     response = callback_function(
#         cell_data,
#         input_values,
#         slider_values,
#         flip_x,
#         flip_y,
#         rotate
#     )

#     return response


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
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
#         Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
#     ],
#     [
#         Input('cell_store', 'data'),
#         Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'action': 'flip_x'}, 'n_clicks'),
#         Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'action': 'flip_y'}, 'n_clicks'),
#         # Add range slider inputs
#         Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
#         Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
#     ],
#     prevent_initial_call=True
# )
# def update_tabless_current_collector(cell_data, input_values, slider_values, flip_x, flip_y, rangeslider_values, input_start_values, input_end_values):

#     callback_function = create_generic_current_collector_callback(
#         CollectorType.TABLESS,
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


# @callback(
#     [
#         Output('cathode_current_collector_a_side_plot', 'figure'),
#         Output('cathode_current_collector_b_side_plot', 'figure'),
#         Output('cathode_current_collector_top_down_plot', 'figure'),
#     ],
#     [
#         Input('cell_store', 'data'),
#         Input('continue_to_design', 'n_clicks'),
#     ],
#     prevent_initial_call=True
# )
# def update_cathode_current_collector_plots(cell_data, continue_to_design):
#     """
#     Update the cathode current collector plots based on the current collector store data.
#     """
#     # get the cell from the cache
#     cell = cache.get(cell_data['cache_key'])

#     # get the current collector from the cell
#     current_collector = get_current_collector_from_cell(cell, ElectrodeType.CATHODE)

#     # get the plots from the current collector
#     a_side_plot = current_collector.get_a_side_view(with_dimensions=False, title='A-Side Current Collector View')
#     b_side_plot = current_collector.get_b_side_view(with_dimensions=False, title='B-Side Current Collector View')
#     top_down_plot = current_collector.get_top_down_view(with_dimensions=False, title='Top-Down Current Collector View')

#     # return the plots
#     return a_side_plot, b_side_plot, top_down_plot

