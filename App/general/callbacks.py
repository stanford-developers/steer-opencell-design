from dash import callback, Output, Input, State, no_update, ctx, ALL
from pathlib import Path
from base64 import b64decode
from uuid import uuid4
from pickle import loads

from database_service import DATA_PATH
from cache_service import cache
from general.store import LANDING_PAGE_IMAGE_URLS

from OpenCell.DataManager import DataManager


@callback(
    [Output('cathode_cc', 'style'),
     Output('anode_cc', 'style'),
     Output('warnings', 'style')],
     Input('tabs-container', 'value'),
    prevent_initial_call=True
)
def show_tab_content(active_tab):

    styles = {'display': 'none'}
    active_style = {'display': 'block'}

    return [
        active_style if active_tab == 'cathode_cc' else styles,
        active_style if active_tab == 'anode_cc' else styles,
        active_style if active_tab == 'warnings' else styles,
    ]


@callback(
    Output('internal_construction_dropdown', 'options'),
    Input('form_factor_dropdown', 'value'),
    prevent_initial_call=True
)
def update_internal_construction_options(form_factor):

    try:
        # get current collector materials from the database
        CURRENT_DIR = Path(__file__).resolve().parent
        DATA_PATH = CURRENT_DIR / '..' / '..' / 'Data' / 'database.db'
        dm = DataManager(DATA_PATH)
        
    except Exception as e:
        print(f"Error initializing DataManager: {e}")
        return no_update

    try:

        options = (
            dm
            .get_data('cells')
            .query(f"form_factor == '{form_factor}'")
            .filter(['internal_construction'])
            .drop_duplicates()
            .internal_construction
            .tolist()
        )

        return [{'label': option, 'value': option} for option in options]
    
    except Exception as e:
        print(f"Error fetching internal construction options: {e}")
        return no_update
        

@callback(
    Output('electrochemical_reference_dropdown', 'options'),
    Input('internal_construction_dropdown', 'value'),
    State('form_factor_dropdown', 'value'),
    prevent_initial_call=True
)
def update_electrochemical_reference_options(internal_construction, form_factor):

    try:
        # get current collector materials from the database
        CURRENT_DIR = Path(__file__).resolve().parent
        DATA_PATH = CURRENT_DIR / '..' / '..' / 'Data' / 'database.db'
        dm = DataManager(DATA_PATH)

    except Exception as e:
        print(f"Error initializing DataManager: {e}")
        return no_update

    try:

        options = (
            dm
            .get_data('cells')
            .query(f"form_factor == '{form_factor}'")
            .query(f"internal_construction == '{internal_construction}'")
            .filter(['reference'])
            .drop_duplicates()
            .reference
            .tolist()
        )

        return [{'label': option, 'value': option} for option in options]
    
    except Exception as e:
        print(f"Error fetching electrochemical reference options: {e}")
        return no_update


@callback(
    Output('cell_name_dropdown', 'options'),
    Input('electrochemical_reference_dropdown', 'value'),
    State('internal_construction_dropdown', 'value'),
    State('form_factor_dropdown', 'value'),
    prevent_initial_call=True
)
def update_cell_name_options(electrochemical_reference, internal_construction, form_factor):

    try:
        # get current collector materials from the database
        CURRENT_DIR = Path(__file__).resolve().parent
        DATA_PATH = CURRENT_DIR / '..' / '..' / 'Data' / 'database.db'
        dm = DataManager(DATA_PATH)

    except Exception as e:
        print(f"Error initializing DataManager: {e}")
        return no_update

    try:

        options = (
            dm
            .get_data('cells')
            .query(f"form_factor == '{form_factor}'")
            .query(f"internal_construction == '{internal_construction}'")
            .query(f"reference == '{electrochemical_reference}'")
            .filter(['name'])
            .drop_duplicates()
            .name
            .tolist()
        )

        return [{'label': option, 'value': option} for option in options]

    except Exception as e:
        print(f"Error fetching cell name options: {e}")
        return no_update
    

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
def get_cell_from_database(contents):

    if contents is None:
        return no_update

    # try establish connection to the database
    try:
        CURRENT_DIR = Path(__file__).resolve().parent
        DATA_PATH = CURRENT_DIR / '..' / '..' / 'Data' / 'database.db'
        dm = DataManager(DATA_PATH)
    except Exception as e:
        print(f"Error initializing DataManager: {e}")
        return no_update
    
    # try and get the serialized cell data from the database
    try:
        cell_data = dm.get_data('cells').query(f"name == '{contents}'").iloc[0]['object']
    except Exception as e:
        print(f"Error fetching cell data from database: {e}")
        return no_update
    
    # Decode the base64 content
    try:
        decoded_data = b64decode(cell_data)
    except Exception as decode_error:
        print(f"Error decoding base64 content: {decode_error}")
        return no_update

    # Deserialize the object using pickle
    try:
        cell = loads(decoded_data)
    except Exception as deserialize_error:
        print(f"Error deserializing pickle data: {deserialize_error}")
        return no_update

    # Generate a new cache key
    new_cc_key = str(uuid4())

    # Store the object in the cache
    cache.set(new_cc_key, cell)

    # Return the cache key to update the store
    return [{'cache_key': new_cc_key}]
    

@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True)
    ],
    [
        Input('upload_cell', 'contents')
    ],
    prevent_initial_call=True
)
def upload_cell(contents):

    try:
        if contents is None:
            return no_update

        # Extract the uploaded file content
        content_type, content_string = contents.split(',')

        # Decode the base64 content
        try:
            decoded_data = b64decode(b64decode(content_string))
        except Exception as decode_error:
            print(f"Error decoding base64 content: {decode_error}")
            return no_update

        # Deserialize the object using pickle
        try:
            current_collector = loads(decoded_data)
        except Exception as deserialize_error:
            print(f"Error deserializing pickle data: {deserialize_error}")
            return no_update

        # Generate a new cache key
        new_cc_key = str(uuid4())

        # Store the object in the cache
        cache.set(new_cc_key, current_collector)
        
        # Return the cache key to update the store
        return [{'cache_key': new_cc_key}]

    except Exception as e:
        print(f"Error in upload callback: {e}")
        return no_update
    

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


