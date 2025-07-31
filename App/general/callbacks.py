from certifi import contents
from dash import callback, Output, Input, State, no_update, ctx, ALL
from pathlib import Path
from base64 import b64decode
from uuid import uuid4
from pickle import loads
from typing import List, Tuple, Dict

from cache_service import cache

from general.store import LANDING_PAGE_IMAGE_URLS
from general.callback_helpers import get_internal_construction_options, get_electrochemical_reference_options, get_cell_name_options


@callback(
    [
        Output('cathode_cc', 'style'),
        Output('anode_cc', 'style'),
        Output('warnings', 'style')
    ],
    Input('tabs-container', 'value'),
    prevent_initial_call=True
)
def show_tab_content(active_tab) -> List:
    """
    Function to show or hide main content based on the active tab.

    Parameters
    ----------
    active_tab : str
        The ID of the currently active tab.
    """
    styles = {'display': 'none'}
    active_style = {'display': 'block'}

    return [
        active_style if active_tab == 'cathode_cc' else styles,
        active_style if active_tab == 'anode_cc' else styles,
        active_style if active_tab == 'warnings' else styles,
    ]


@callback(
    [
        Output('internal_construction_dropdown', 'options'),
        Output('form_factor_dropdown', 'value'),
    ],
    [
        Input('form_factor_dropdown', 'value'),
        Input({'type': 'cell_schematic_button', 'key': ALL}, 'n_clicks')
    ],
    [
        State('form_factor_dropdown', 'options'),
    ],
    prevent_initial_call=True
)
def update_internal_construction_options(
    form_factor, 
    form_factor_schematic_button_clicks, 
    form_factor_options
) -> Tuple[List[dict], str]:
    
    # get the triggered ID to determine which input caused the callback
    trigger = ctx.triggered_id

    # If the form factor dropdown is triggered, return options based on the selected form factor
    if trigger == 'form_factor_dropdown':
        return get_internal_construction_options(form_factor), no_update
    
    # If a cell schematic button is clicked, return options based on the button key
    elif isinstance(trigger, dict) and trigger['type'] == 'cell_schematic_button':

        form_factor = trigger['key']

        # If the form factor is not in the options, return no update
        if form_factor not in [option['value'] for option in form_factor_options]:
            return no_update, no_update
        
        # Otherwise, return the options based on the form factor
        return get_internal_construction_options(form_factor), form_factor
    
    else:
        # If no valid trigger, return no update
        return no_update, no_update


@callback(
    [
        Output('electrochemical_reference_dropdown', 'options'),
        Output('internal_construction_dropdown', 'value'),
    ],
    [
        Input('internal_construction_dropdown', 'value'),
        Input({'type': 'cell_schematic_button', 'key': ALL}, 'n_clicks')
    ],
    [
        State('form_factor_dropdown', 'value'),
        State('internal_construction_dropdown', 'options'),
    ],
    prevent_initial_call=True
)
def update_electrochemical_reference_options(
    internal_construction, 
    internal_construction_button_clicks, 
    form_factor, 
    internal_construction_options
):
    trigger = ctx.triggered_id

    # If the internal construction dropdown is triggered, return options based on the selected internal construction
    if trigger == 'internal_construction_dropdown':
        return get_electrochemical_reference_options(internal_construction, form_factor), no_update

    elif isinstance(trigger, dict) and trigger['type'] == 'cell_schematic_button':

        internal_construction = trigger['key']

        # If the internal construction is not in the options, return no update
        if internal_construction not in [option['value'] for option in internal_construction_options]:
            return no_update, no_update
        
        # Otherwise, return the options based on the internal construction and form factor
        return get_electrochemical_reference_options(internal_construction, form_factor), internal_construction
    
    else:
        # If no valid trigger, return no update
        return no_update, no_update


@callback(
    [
        Output('cell_name_dropdown', 'options'),
        Output('electrochemical_reference_dropdown', 'value'),
    ],
    [
        Input('electrochemical_reference_dropdown', 'value'),
        Input({'type': 'cell_schematic_button', 'key': ALL}, 'n_clicks'),
    ],
    [
        State('internal_construction_dropdown', 'value'),
        State('form_factor_dropdown', 'value'),
        State('electrochemical_reference_dropdown', 'options'),
    ],
    prevent_initial_call=True
)
def update_cell_name_options(
    electrochemical_reference, 
    electrochemical_reference_button_clicks, 
    internal_construction, 
    form_factor, 
    electrochemical_reference_options
):

    trigger = ctx.triggered_id

    # If the electrochemical reference dropdown is triggered, return options based on the selected electrochemical reference
    if trigger == 'electrochemical_reference_dropdown':
        return get_cell_name_options(internal_construction, electrochemical_reference, form_factor), no_update
    
    elif isinstance(trigger, dict) and trigger['type'] == 'cell_schematic_button':
        electrochemical_reference = trigger['key']

        # If the electrochemical reference is not in the options, return no update
        if electrochemical_reference not in [option['value'] for option in electrochemical_reference_options]:
            return no_update, no_update
        
        # Otherwise, return the options based on the electrochemical reference, internal construction, and form factor
        return get_cell_name_options(internal_construction, electrochemical_reference, form_factor), electrochemical_reference

    else:
        # If no valid trigger, return no update
        return no_update, no_update


@callback(
    [
        Output({'type': 'cell_schematic_image', 'key': ALL}, 'style'),
    ],
    [
        Input('form_factor_dropdown', 'options'),
        Input('internal_construction_dropdown', 'options'),
        Input('electrochemical_reference_dropdown', 'options'),
        Input('form_factor_dropdown', 'value'),
        Input('internal_construction_dropdown', 'value'),
        Input('electrochemical_reference_dropdown', 'value'),
    ],
    [
        State({'type': 'cell_schematic_image', 'key': ALL}, 'style'),
    ]
)
def update_landing_image_alpha(
    form_factor_options, 
    internal_construction_options, 
    electrochemical_reference_options, 
    form_factor_value,
    internal_construction_value,
    electrochemical_reference_value,
    current_styles
):
    # Ensure current_styles is initialized correctly
    if not current_styles:
        current_styles = [{'width': '40%', 'opacity': '20%'} for _ in LANDING_PAGE_IMAGE_URLS]

    # Flatten options into a single list
    available_options = [item['value'] for item in form_factor_options + internal_construction_options + electrochemical_reference_options]

    # Reset all styles to default opacity (10%)
    for style in current_styles:
        style['opacity'] = '10%'

    # Update styles for matching keys in available options
    for idx, key in enumerate(LANDING_PAGE_IMAGE_URLS.keys()):
        if key in available_options:
            current_styles[idx]['opacity'] = '50%'  # Set to 50% if key is in available options

        # Set opacity to 100% if the key matches any of the value inputs
        if key in [form_factor_value, internal_construction_value, electrochemical_reference_value]:
            current_styles[idx]['opacity'] = '100%'

    return [current_styles]


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True)
    ],
    [
        Input('cell_name_dropdown', 'value')
    ],
    prevent_initial_call=True
)
def get_cell_from_database(cell_name: str) -> Dict:
    """
    Callback to fetch the cell from the database based on the selected cell name.

    Parameters
    ----------
    contents : str
        The selected cell name from the dropdown.
    """
    from general.callback_helpers import get_cell_from_database, set_cell_to_cache

    # If contents is None, return no update
    if cell_name is None:
        return no_update

    cell = get_cell_from_database(cell_name)
    new_key = set_cell_to_cache(cell)
    return [{'cache_key': new_key}]


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True)
    ],
    [
        Input('upload_cell', 'contents')
    ],
    prevent_initial_call=True
)
def upload_cell(pickled_cell):
    """
    Callback to handle the upload of a cell object from a file.

    Parameters
    ----------
    pickled_cell : str
        The base64 encoded string of the pickled cell object.
    
    Returns
    -------
    List[Dict]
        A list containing a dictionary with the cache key of the uploaded cell.
    """
    from general.callback_helpers import set_cell_to_cache

    # If pickled_cell is None, return no update
    if pickled_cell is None:
        return no_update

    # Extract the uploaded file content
    content_type, content_string = pickled_cell.split(',')

    # Decode the base64 content
    try:
        decoded_data = b64decode(b64decode(content_string))
    except Exception as decode_error:
        print(f"Error decoding base64 content: {decode_error}")
        return no_update

    cell = loads(decoded_data)

    new_key = set_cell_to_cache(cell)
    
    # Return the cache key to update the store
    return [{'cache_key': new_key}]


@callback(
    [
        Output('cell_type_panel', 'style'),
        Output('tabs_panel', 'style'),
    ],
    [
        Input('continue_to_design', 'n_clicks'),
        Input('back_to_cell_type', 'n_clicks'),
    ],
    [
        State('cell_type_panel', 'style'),
        State('tabs_panel', 'style'),
    ],
    prevent_initial_call=True
)
def show_and_hide_cell_type_and_tabs(continue_clicks, back_clicks, continue_style, back_style):
    """
    Show or hide the cell type and tabs based on button clicks.
    """
    ctx_id = ctx.triggered_id

    if ctx_id == 'continue_to_design':
        continue_style['display'] = 'none'
        back_style['display'] = 'block'

    elif ctx_id == 'back_to_cell_type':
        continue_style['display'] = 'flex'
        back_style['display'] = 'none'

    return continue_style, back_style


