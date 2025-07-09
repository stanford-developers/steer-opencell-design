from dash import callback, Input, Output, ctx, State, no_update, MATCH, ALL
import numpy as np
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
            property = 'material'
            value = material

        # Handle slider/input updates
        elif isinstance(triggered_id, dict) and 'property' in triggered_id:
            property = triggered_id['property']
            property_index = PUNCHED_PARAMETER_LIST.index(property)
            value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]
            current_collector.__setattr__(property, value)

        parameter_list = [current_collector.__getattribute__(param) for param in PUNCHED_PARAMETER_LIST]
        min_values = [current_collector.__getattribute__(f"{param}_range")[0] for param in PUNCHED_PARAMETER_LIST]
        max_values = [current_collector.__getattribute__(f"{param}_range")[1] for param in PUNCHED_PARAMETER_LIST]

        # ensure parameters are within their defined ranges
        for i, (p, min, max) in enumerate(zip(parameter_list, min_values, max_values)):
            if p < min:
                p = min
                current_collector.__setattr__(PUNCHED_PARAMETER_LIST[i], min)
                parameter_list[i] = min
            elif p > max:
                p = max
                current_collector.__setattr__(PUNCHED_PARAMETER_LIST[i], max)
                parameter_list[i] = max

        marks_list = [current_collector.__getattribute__(f"{param}_marks") for param in PUNCHED_PARAMETER_LIST]

        # Update cache and generate parameter list
        new_cc_key = str(uuid4())
        cache.set(new_cc_key, current_collector)

        return (
            {'cache_key': new_cc_key},
            parameter_list,
            parameter_list,
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
