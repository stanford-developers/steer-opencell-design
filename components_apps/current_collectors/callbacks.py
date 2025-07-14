from dash import callback, Input, Output, ctx, State, no_update, MATCH, ALL
import base64
import pickle
import time

from cache_service import cache
from uuid import uuid4

from SteerEnergyStorage.Materials.CurrentCollectors import *
from SteerEnergyStorage.Materials.RawMaterials import *

from current_collectors.layouts import *


PUNCHED_PARAMETER_LIST = [
    'width',
    'height',
    'thickness',
    'tab_width',
    'tab_height',
    'tab_position',
    'coated_tab_height',
    'insulation_width',
    'cost',
    'mass',
    'coated_area',
    'insulation_area',
    'datum_x',
    'datum_y',
    'datum_z',
]

CC_MATERIAL_PARAMETER_LIST = [
    'density',
    'specific_cost',
]

@callback(
    [
        Output('cathode_current_collector_material_store', 'data'),
        Output('cathode_material_selector', 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'marks'),
    ],
    [
        Input('cathode_material_selector', 'value'),
        Input('cathode_current_collector_material_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'slider'}, 'value')
    ]
)
def update_punched_current_collector(
    material_selector,
    current_collector_material_data,
    input_values,
    slider_values
):
    try:
        material = cache.get(current_collector_material_data['cache_key'])
        triggered_id = ctx.triggered_id

        if triggered_id == 'cathode_material_selector':
            material = CurrentCollectorMaterial.from_database(material_selector)

        # Handle slider/input updates
        elif isinstance(triggered_id, dict) and 'property' in triggered_id:
            property = triggered_id['property']
            property_index = CC_MATERIAL_PARAMETER_LIST.index(property)
            value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]
            material.__setattr__(property, value)

        # Update cache and generate parameter list
        new_cc_key = str(uuid4())
        cache.set(new_cc_key, material)

        parameter_list = [material.__getattribute__(param) for param in CC_MATERIAL_PARAMETER_LIST]
        min_values = [material.__getattribute__(f"{param}_range")[0] for param in CC_MATERIAL_PARAMETER_LIST]
        max_values = [material.__getattribute__(f"{param}_range")[1] for param in CC_MATERIAL_PARAMETER_LIST]
        marks_list = [material.__getattribute__(f"{param}_marks") for param in CC_MATERIAL_PARAMETER_LIST]

        return (
            {'cache_key': new_cc_key},
            material.name,
            parameter_list,
            parameter_list,
            min_values,
            max_values,
            marks_list
        )
    
    except Exception as e:
        print(f"Error in callback: {e}")
        return no_update, no_update*len(PUNCHED_PARAMETER_LIST), no_update*len(PUNCHED_PARAMETER_LIST), no_update*len(PUNCHED_PARAMETER_LIST), no_update*len(PUNCHED_PARAMETER_LIST), no_update, no_update, no_update


@callback(
    Output('cathode_current_collector_design', 'value'),
    [
        Input('cathode_current_collector_store', 'data'),
        Input('cathode_current_collector_store', 'modified_timestamp')
    ],
    prevent_initial_call=True
)
def update_cathode_current_collector_design(data, data_ts):
    """
    Update the cathode current collector design based on the current collector store data.
    """
    try:
        current_collector = cache.get(data['cache_key'])

        if type(current_collector) == PunchedCurrentCollector:
            return 'punched'
        elif type(current_collector) == NotchedCurrentCollector:
            return 'notched'
        elif type(current_collector) == TablessCurrentCollector:
            return 'tabless'
        elif type(current_collector) == TabWeldedCurrentCollector:
            return 'tabbed'

    except Exception as e:
        return None
    

@callback(
    [Output('cathode_punched_design_parameters', 'style'),
     Output('cathode_notched_design_parameters', 'style'),
     Output('cathode_tabless_design_parameters', 'style'),
     Output('cathode_tabbed_design_parameters', 'style')],
    Input('cathode_current_collector_design', 'value')
)
def update_cathode_current_collector_design_parameters(design):
    """
    Update the cathode current collector design parameters based on the current collector store data.
    """

    styles = {'display': 'none'}
    active_style = {'display': 'block'}

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
        Output('cathode_current_collector_store', 'data'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks')
    ],
    [
        Input('cathode_current_collector_store', 'data'),
        Input('cathode_current_collector_material_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value')
    ],
    prevent_initial_call=True
)
def update_punched_current_collector(
    current_collector_data,
    material_data,
    input_values,
    slider_values
):
    try:
        current_collector = cache.get(current_collector_data['cache_key'])
        triggered_id = ctx.triggered_id

        # Handle material updates
        if triggered_id == 'cathode_current_collector_material_store':
            material = cache.get(material_data['cache_key'])
            current_collector.material = material

        # Handle slider/input updates
        elif isinstance(triggered_id, dict) and 'property' in triggered_id:
            property = triggered_id['property']
            property_index = PUNCHED_PARAMETER_LIST.index(property)
            value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]

            current_collector.__setattr__(property, value)

            # Validate dependent properties
            for param in PUNCHED_PARAMETER_LIST:
                if param != property:  # Skip the updated property
                    param_range = current_collector.__getattribute__(f"{param}_range")
                    param_value = current_collector.__getattribute__(param)
                    if param_value < param_range[0]:
                        current_collector.__setattr__(param, param_range[0])
                    elif param_value > param_range[1]:
                        current_collector.__setattr__(param, param_range[1])

        value_list = [current_collector.__getattribute__(param) for param in PUNCHED_PARAMETER_LIST]
        min_values = [current_collector.__getattribute__(f"{param}_range")[0] for param in PUNCHED_PARAMETER_LIST]
        max_values = [current_collector.__getattribute__(f"{param}_range")[1] for param in PUNCHED_PARAMETER_LIST]
        marks_list = [current_collector.__getattribute__(f"{param}_marks") for param in PUNCHED_PARAMETER_LIST]

        # Update cache and generate parameter list
        new_cc_key = str(uuid4())
        cache.set(new_cc_key, current_collector)

        return (
            {'cache_key': new_cc_key},
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
        )
    
    except Exception as e:
        print(f"Error in callback: {e}")
        return no_update, no_update*len(PUNCHED_PARAMETER_LIST), no_update*len(PUNCHED_PARAMETER_LIST), no_update*len(PUNCHED_PARAMETER_LIST), no_update*len(PUNCHED_PARAMETER_LIST), no_update, no_update, no_update


@callback(
    [
        Output('cathode_a_side_plot', 'figure'),
        Output('cathode_b_side_plot', 'figure'),
    ],
    [
        Input('cathode_current_collector_store', 'data'),
    ]
)
def update_cathode_current_collector_plots(data):
    """
    Update the cathode current collector plots based on the current collector store data.
    """
    try:
        current_collector = cache.get(data['cache_key'])
        a_side_plot = current_collector.get_a_side_view(with_dimensions=False)
        b_side_plot = current_collector.get_b_side_view(with_dimensions=False)

        return a_side_plot, b_side_plot
    
    except Exception as e:
        print(f"Error in callback: {e}")
        return no_update, no_update


@callback(
    Output('download_cathode_current_collector', 'data'),
    Input('download_cathode_current_collector_button', 'n_clicks'),
    State('cathode_current_collector_store', 'data'),
    prevent_initial_call=True
)
def download_cathode_current_collector(n_clicks, current_collector_data):
    
    try:
        # Retrieve the current collector object from the cache
        current_collector = cache.get(current_collector_data['cache_key'])

        # Serialize the object using pickle
        try:
            serialized_data = pickle.dumps(current_collector)
        except Exception as serialize_error:
            print(f"Error serializing current collector: {serialize_error}")
            return None
        
        # base64 encode the serialized data
        try:
            encoded_data = base64.b64encode(serialized_data).decode('utf-8')
        except Exception as encode_error:
            print(f"Error encoding serialized data to base64: {encode_error}")
            return None

        # Return the serialized data as a downloadable file
        return dict(
            content=encoded_data,
            filename='current_collector.pkl'
        )
    
    except Exception as e:
        print(f"Error in download callback: {e}")
        return None
    

@callback(
    Output('cathode_current_collector_store', 'data', allow_duplicate=True),
    Input('upload_cathode_current_collector', 'contents'),
    prevent_initial_call=True
)
def upload_cathode_current_collector(contents):

    try:
        if contents is None:
            return no_update

        # Extract the uploaded file content
        content_type, content_string = contents.split(',')

        print(f"Content type: {content_type[:100]}")

        # Decode the base64 content
        try:
            decoded_data = base64.b64decode(base64.b64decode(content_string))
        except Exception as decode_error:
            print(f"Error decoding base64 content: {decode_error}")
            return no_update

        # Deserialize the object using pickle
        try:
            current_collector = pickle.loads(decoded_data)
        except Exception as deserialize_error:
            print(f"Error deserializing pickle data: {deserialize_error}")
            return no_update

        # Generate a new cache key
        new_cc_key = str(uuid4())

        # Store the object in the cache
        cache.set(new_cc_key, current_collector)
        
        # Return the cache key to update the store
        return {'cache_key': new_cc_key}

    except Exception as e:
        print(f"Error in upload callback: {e}")
        return no_update
    


