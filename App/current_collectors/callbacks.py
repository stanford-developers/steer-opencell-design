from dash import callback, Input, Output, ctx, State, no_update, MATCH, ALL

from OpenCell.Materials.CurrentCollectors import _TapeCurrentCollector
from cache_service import cache
from uuid import uuid4

from OpenCell.Materials.CurrentCollectors import _TapeCurrentCollector
from OpenCell.Materials.CurrentCollectors import *
from OpenCell.Materials.RawMaterials import *

from current_collectors.layouts import *
from current_collectors.callbacks import CURRENT_COLLECTOR_DESIGNS



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

PUNCHED_SETTABLE_PARAMETERS = [
    'width',
    'height',
    'thickness',
    'tab_width',
    'tab_height',
    'tab_position',
    'coated_tab_height',
    'insulation_width',
    'datum_x',
    'datum_y',
    'datum_z',
]



NOTCHED_PARAMETER_LIST = [
    'length',
    'width',
    'thickness',
    'tab_width',
    'tab_height',
    'tab_spacing',
    'tab_gap',
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

NOTCHED_SETTABLE_PARAMETERS = [
    'length',
    'width',
    'thickness',
    'tab_width',
    'tab_height',
    'tab_spacing',
    'tab_gap',
    'coated_tab_height',
    'insulation_width',
    'datum_x',
    'datum_y',
    'datum_z',
]



TABLESS_PARAMETER_LIST = [
    'length',
    'width',
    'thickness',
    'coated_width',
    'insulation_width',
    'cost',
    'mass',
    'coated_area',
    'insulation_area',
    'datum_x',
    'datum_y',
    'datum_z',
]

TABLESS_SETTABLE_PARAMETERS = [
    'length',
    'width',
    'thickness',
    'coated_width',
    'insulation_width',
    'datum_x',
    'datum_y',
    'datum_z',
]



TABBED_PARAMETER_LIST = [
    'length',
    'width',
    'thickness',
    'skip_coat_width',
    'cost',
    'mass',
    'coated_area',
    'datum_x',
    'datum_y',
    'datum_z',
]

TABBED_SETTABLE_PARAMETERS = [
    'length',
    'width',
    'thickness',
    'skip_coat_width',
    'datum_x',
    'datum_y',
    'datum_z',
]



TAPE_RANGE_SLIDER_PARAMETERS = [
    'a_side_coated_section',
    'b_side_coated_section',
]

CC_MATERIAL_PARAMETER_LIST = [
    'density',
    'specific_cost',
]



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
def update_cathode_dropdown_and_design(data, current_style, current_options):
    """
    Update the cathode current collector design dropdown menu options, style, and value
    based on the current collector store data.
    """
    # get the cell from the cache
    cell = cache.get(data['cache_key'])

    # get the current collector from the cell
    current_collector = cell

    # If the current collector is None, return no_update
    if current_collector is None:
        return current_options, current_style, no_update

    # Initialize outputs
    options = []
    value = None

    # Determine the type of the current collector and update outputs accordingly
    if type(current_collector) == PunchedCurrentCollector:
        current_style['display'] = 'none'
        options = [{'label': 'Punched', 'value': 'punched'}]
        value = 'punched'
    elif type(current_collector) == NotchedCurrentCollector:
        current_style['display'] = 'block'
        options = [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched']
        value = 'notched'
    elif type(current_collector) == TablessCurrentCollector:
        current_style['display'] = 'block'
        options = [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched']
        value = 'tabless'
    elif type(current_collector) == TabWeldedCurrentCollector:
        current_style['display'] = 'block'
        options = [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched']
        value = 'tabbed'
    elif type(current_collector) == _TapeCurrentCollector:
        current_style['display'] = 'none'
        options = [{'label': item, 'value': item.lower()} for item in CURRENT_COLLECTOR_DESIGNS if item != 'Punched']

    return options, current_style, value


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode_current_collector_material_selector', 'value'),
        Output({'electrode': 'cathode', 'object': 'material', 'property': ALL, 'subtype': 'input'}, 'value'),
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
    slider_values
):
    
    def generate_material_parameters(material):
        """Helper function to generate parameter lists for the material."""
        parameter_list = [getattr(material, param) for param in CC_MATERIAL_PARAMETER_LIST]
        min_values = [getattr(material, f"{param}_range")[0] for param in CC_MATERIAL_PARAMETER_LIST]
        max_values = [getattr(material, f"{param}_range")[1] for param in CC_MATERIAL_PARAMETER_LIST]
        marks_list = [getattr(material, f"{param}_marks") for param in CC_MATERIAL_PARAMETER_LIST]
        return parameter_list, min_values, max_values, marks_list

    triggered_id = ctx.triggered_id
    cell = cache.get(cell_data['cache_key'])
    current_collector = cell

    # If the cell store is triggered, get the current collector material from the cell
    if triggered_id == 'cell_store':

        # get the material from the current_collector
        material = current_collector.material

        # generate the parameter lists
        parameter_list, min_values, max_values, marks_list = generate_material_parameters(material)
        
        # and return the values
        return (
            no_update,
            material.name,
            parameter_list,
            parameter_list,
            min_values,
            max_values,
            marks_list
        )

    # If the material selector is triggered, update the material
    elif triggered_id == 'cathode_current_collector_material_selector':

        # get the new material from the database
        material = CurrentCollectorMaterial.from_database(material_selector)

        # assign the material to the current_collector
        current_collector.material = material

        # make the new key and store in cache
        cell = current_collector
        new_cc_key = str(uuid4())
        cache.set(new_cc_key, cell)

        # generate the parameter lists
        parameter_list, min_values, max_values, marks_list = generate_material_parameters(material)

        # and return the values
        return (
            {'cache_key': new_cc_key},
            material.name,
            parameter_list,
            parameter_list,
            min_values,
            max_values,
            marks_list
        )

    # Handle slider/input updates
    elif isinstance(triggered_id, dict) and 'property' in triggered_id:

        # determine which property was triggered
        property = triggered_id['property']
        property_index = CC_MATERIAL_PARAMETER_LIST.index(property)
        value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]

        # get the material
        material = current_collector.material

        # set the property of the material
        setattr(material, property, value)

        # assign the material back to the current_collector
        current_collector.material = material

        # make the new key and store in cache
        cell = current_collector
        new_cc_key = str(uuid4())
        cache.set(new_cc_key, cell)

        # generate the parameter lists
        parameter_list, min_values, max_values, marks_list = generate_material_parameters(material)

        # return the updated values
        return (
            {'cache_key': new_cc_key},
            material.name,
            parameter_list,
            parameter_list,
            min_values,
            max_values,
            marks_list
        )


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output('cathode_current_collector_tab_material_selector', 'value'),
        Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'marks'),
    ],
    [
        Input('cell_store', 'data'),
        Input('cathode_current_collector_tab_material_selector', 'value'),
        Input({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tab_material', 'property': ALL, 'subtype': 'slider'}, 'value'),
    ],
    prevent_initial_call=True
)
def update_cathode_current_collector_tab_material(
    cell_data,
    material_selector,
    input_values,
    slider_values
):
    
    def generate_material_parameters(material):
        """Helper function to generate parameter lists for the material."""
        parameter_list = [getattr(material, param) for param in CC_MATERIAL_PARAMETER_LIST]
        min_values = [getattr(material, f"{param}_range")[0] for param in CC_MATERIAL_PARAMETER_LIST]
        max_values = [getattr(material, f"{param}_range")[1] for param in CC_MATERIAL_PARAMETER_LIST]
        marks_list = [getattr(material, f"{param}_marks") for param in CC_MATERIAL_PARAMETER_LIST]
        return parameter_list, min_values, max_values, marks_list

    triggered_id = ctx.triggered_id
    cell = cache.get(cell_data['cache_key'])
    current_collector = cell

    # no update if the current collector is not a TabWeldedCurrentCollector and doesnt have a weld tab
    try:
        weld_tab = current_collector.weld_tab
    except Exception:
        return (
            no_update,
            no_update,
            [no_update] * len(CC_MATERIAL_PARAMETER_LIST),
            [no_update] * len(CC_MATERIAL_PARAMETER_LIST),
            [no_update] * len(CC_MATERIAL_PARAMETER_LIST),
            [no_update] * len(CC_MATERIAL_PARAMETER_LIST),
            [no_update] * len(CC_MATERIAL_PARAMETER_LIST),
        )

    # If the cell store is triggered, get the current collector material from the cell
    if triggered_id == 'cell_store':

        # get the material from tab
        material = weld_tab.material

        # generate the parameter lists
        parameter_list, min_values, max_values, marks_list = generate_material_parameters(material)
        
        # and return the values
        return (
            no_update,
            material.name,
            parameter_list,
            parameter_list,
            min_values,
            max_values,
            marks_list
        )

    # If the material selector is triggered, update the material
    elif triggered_id == 'cathode_current_collector_tab_material_selector':

        # get the new material from the database
        material = CurrentCollectorMaterial.from_database(material_selector)

        # make the new key and store in cache
        weld_tab.material = material
        current_collector.weld_tab = weld_tab
        cell = current_collector

        new_cc_key = str(uuid4())
        cache.set(new_cc_key, cell)

        # generate the parameter lists
        parameter_list, min_values, max_values, marks_list = generate_material_parameters(material)

        # and return the values
        return (
            {'cache_key': new_cc_key},
            material.name,
            parameter_list,
            parameter_list,
            min_values,
            max_values,
            marks_list
        )

    # Handle slider/input updates
    elif isinstance(triggered_id, dict) and 'property' in triggered_id:

        # determine which property was triggered
        property = triggered_id['property']
        property_index = CC_MATERIAL_PARAMETER_LIST.index(property)
        value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]

        # get the material
        material = weld_tab.material

        # set the property of the material
        setattr(material, property, value)

        # assign the material back to the current_collector
        weld_tab.material = material

        # make the new key and store in cache
        current_collector.weld_tab = weld_tab
        cell = current_collector
        new_cc_key = str(uuid4())
        cache.set(new_cc_key, cell)

        # generate the parameter lists
        parameter_list, min_values, max_values, marks_list = generate_material_parameters(material)

        # return the updated values
        return (
            {'cache_key': new_cc_key},
            material.name,
            parameter_list,
            parameter_list,
            min_values,
            max_values,
            marks_list
        )


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
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks')
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'action': 'flip_x'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'punched_current_collector', 'action': 'flip_y'}, 'n_clicks'),
    ],
    prevent_initial_call=True
)
def update_punched_current_collector(
    cell_data,
    input_values,
    slider_values,
    flip_x,
    flip_y
):
    
    def generate_parameters(current_collector):
        """Helper function to generate parameter lists for the material."""
        parameter_list = [getattr(current_collector, param) for param in PUNCHED_PARAMETER_LIST]
        min_values = [getattr(current_collector, f"{param}_range")[0] for param in PUNCHED_PARAMETER_LIST]
        max_values = [getattr(current_collector, f"{param}_range")[1] for param in PUNCHED_PARAMETER_LIST]
        marks_list = [getattr(current_collector, f"{param}_marks") for param in PUNCHED_PARAMETER_LIST]
        return parameter_list, min_values, max_values, marks_list

    triggered_id = ctx.triggered_id
    cell = cache.get(cell_data['cache_key'])

    # get the cathode current collector from the cell
    current_collector = cell

    # Check if the current collector is a PunchedCurrentCollector. If not, return no_update
    if type(current_collector) != PunchedCurrentCollector:
        return (
            no_update,
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
        )

    # If the cell store is triggered, get the current collector from the cell
    if triggered_id == 'cell_store':
        
        # generate the parameter lists
        value_list, min_values, max_values, marks_list = generate_parameters(current_collector)

        return (
            no_update,
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
        )
        
    # Handle slider/input updates
    elif isinstance(triggered_id, dict) and 'property' in triggered_id:

        # determine which property was triggered
        property = triggered_id['property']
        property_index = PUNCHED_PARAMETER_LIST.index(property)
        value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]

        # set the property of the current collector
        setattr(current_collector, property, value)

        # Validate dependent properties
        for param in PUNCHED_SETTABLE_PARAMETERS:
            if param != property:  # Skip the updated property
                param_range = getattr(current_collector, f"{param}_range")
                param_value = getattr(current_collector, param)
                if param_value < param_range[0]:
                    setattr(current_collector, param, param_range[0])
                elif param_value > param_range[1]:
                    setattr(current_collector, param, param_range[1])

        value_list, min_values, max_values, marks_list = generate_parameters(current_collector)

        # update the cell data with the new current collector
        cell = current_collector

        # make the new key and store in cache
        cell_data['cache_key'] = str(uuid4())
        cache.set(cell_data['cache_key'], cell)

        # return the updated values
        return (
            {'cache_key': cell_data['cache_key']},
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
        )
    
    elif isinstance(triggered_id, dict) and 'action' in triggered_id:

        # Handle flip actions
        if triggered_id['action'] == 'flip_x':
            current_collector.flip(axis='x')
        elif triggered_id['action'] == 'flip_y':
            current_collector.flip(axis='y')
            
        # update the cell data with the new current collector
        cell = current_collector

        # make the new key and store in cache
        cell_data['cache_key'] = str(uuid4())
        cache.set(cell_data['cache_key'], cell)

        return (
            {'cache_key': cell_data['cache_key']},
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
            [no_update] * len(PUNCHED_PARAMETER_LIST),
        )


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'action': 'flip_x'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'action': 'flip_y'}, 'n_clicks'),
        # Add range slider inputs
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'notched_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
    ],
    prevent_initial_call=True
)
def update_notched_current_collector(
    cell_data,
    input_values,
    slider_values,
    flip_x,
    flip_y,
    rangeslider_values,
    input_start_values,
    input_end_values
):
    
    def generate_parameters(current_collector):
        """Helper function to generate parameter lists for the material."""
        parameter_list = [getattr(current_collector, param) for param in NOTCHED_PARAMETER_LIST]
        min_values = [getattr(current_collector, f"{param}_range")[0] for param in NOTCHED_PARAMETER_LIST]
        max_values = [getattr(current_collector, f"{param}_range")[1] for param in NOTCHED_PARAMETER_LIST]
        marks_list = [getattr(current_collector, f"{param}_marks") for param in NOTCHED_PARAMETER_LIST]
        return parameter_list, min_values, max_values, marks_list
    
    def generate_rangeslider_values(current_collector):
        """Generate the values for the range slider."""
        parameter_list = [getattr(current_collector, param) for param in TAPE_RANGE_SLIDER_PARAMETERS]
        start_list = [p[0] for p in parameter_list]
        end_list = [p[1] for p in parameter_list]
        min_val = [getattr(current_collector, f"{param}_range")[0] for param in TAPE_RANGE_SLIDER_PARAMETERS]
        max_val = [getattr(current_collector, f"{param}_range")[1] for param in TAPE_RANGE_SLIDER_PARAMETERS]
        range_marks_list = [getattr(current_collector, f"{param}_marks") for param in TAPE_RANGE_SLIDER_PARAMETERS]
        return parameter_list, start_list, end_list, min_val, max_val, range_marks_list

    triggered_id = ctx.triggered_id
    cell = cache.get(cell_data['cache_key'])

    # get the cathode current collector from the cell
    current_collector = cell

    # Check if the current collector is a NotchedCurrentCollector. If not, return no_update
    if type(current_collector) != NotchedCurrentCollector:
        return (
            no_update,
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
        )

    # If the cell store is triggered, get the current collector from the cell
    if triggered_id == 'cell_store':
        
        # generate the parameter lists
        value_list, min_values, max_values, marks_list = generate_parameters(current_collector)

        # generate the range slider values
        range_value_list, start_list, end_list, min_val, max_val, range_marks_list = generate_rangeslider_values(current_collector)

        return (
            no_update,
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
            range_value_list,
            start_list,
            end_list,
            min_val,
            max_val,
            range_marks_list
        )
        
    # Handle slider/input updates
    elif isinstance(triggered_id, dict) and 'property' in triggered_id:

        # determine which property was triggered
        property = triggered_id['property']
        
        # Handle range slider properties
        if property in TAPE_RANGE_SLIDER_PARAMETERS:

            range_property_index = TAPE_RANGE_SLIDER_PARAMETERS.index(property)
            
            if triggered_id['subtype'] == 'rangeslider':
                # Range slider was moved
                value = rangeslider_values[range_property_index]
            elif triggered_id['subtype'] == 'input_start':
                # Start input was changed
                current_value = getattr(current_collector, property)
                value = (input_start_values[range_property_index], current_value[1])
            elif triggered_id['subtype'] == 'input_end':
                # End input was changed
                current_value = getattr(current_collector, property)
                value = (current_value[0], input_end_values[range_property_index])
            
            # Set the property as a tuple
            setattr(current_collector, property, value)
            
        # Handle regular slider/input properties  
        elif property in NOTCHED_PARAMETER_LIST:
            property_index = NOTCHED_PARAMETER_LIST.index(property)
            value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]
            setattr(current_collector, property, value)

        # Validate dependent properties for regular parameters only
        for param in NOTCHED_SETTABLE_PARAMETERS:
            if param != property:  # Skip the updated property
                param_range = getattr(current_collector, f"{param}_range")
                param_value = getattr(current_collector, param)
                if param_value < param_range[0]:
                    setattr(current_collector, param, param_range[0])
                elif param_value > param_range[1]:
                    setattr(current_collector, param, param_range[1])

        value_list, min_values, max_values, marks_list = generate_parameters(current_collector)
        range_value_list, start_list, end_list, min_val, max_val, range_marks_list = generate_rangeslider_values(current_collector)

        # update the cell data with the new current collector
        cell = current_collector

        # make the new key and store in cache
        cell_data['cache_key'] = str(uuid4())
        cache.set(cell_data['cache_key'], cell)

        # return the updated values
        return (
            {'cache_key': cell_data['cache_key']},
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
            range_value_list,
            start_list,
            end_list, 
            min_val,
            max_val,
            range_marks_list
        )
    
    elif isinstance(triggered_id, dict) and 'action' in triggered_id:

        # Handle flip actions
        if triggered_id['action'] == 'flip_x':
            current_collector.flip(axis='x')
        elif triggered_id['action'] == 'flip_y':
            current_collector.flip(axis='y')
            
        # update the cell data with the new current collector
        cell = current_collector

        # make the new key and store in cache
        cell_data['cache_key'] = str(uuid4())
        cache.set(cell_data['cache_key'], cell)

        return (
            {'cache_key': cell_data['cache_key']},
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(NOTCHED_PARAMETER_LIST),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
        )


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'action': 'flip_x'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'action': 'flip_y'}, 'n_clicks'),
        # Add range slider inputs
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabless_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
    ],
    prevent_initial_call=True
)
def update_tabless_current_collector(
    cell_data,
    input_values,
    slider_values,
    flip_x,
    flip_y,
    rangeslider_values,
    input_start_values,
    input_end_values
):
    
    def generate_parameters(current_collector):
        """Helper function to generate parameter lists for the material."""
        parameter_list = [getattr(current_collector, param) for param in TABLESS_PARAMETER_LIST]
        min_values = [getattr(current_collector, f"{param}_range")[0] for param in TABLESS_PARAMETER_LIST]
        max_values = [getattr(current_collector, f"{param}_range")[1] for param in TABLESS_PARAMETER_LIST]
        marks_list = [getattr(current_collector, f"{param}_marks") for param in TABLESS_PARAMETER_LIST]
        return parameter_list, min_values, max_values, marks_list
    
    def generate_rangeslider_values(current_collector):
        """Generate the values for the range slider."""
        parameter_list = [getattr(current_collector, param) for param in TAPE_RANGE_SLIDER_PARAMETERS]
        start_list = [p[0] for p in parameter_list]
        end_list = [p[1] for p in parameter_list]
        min_val = [getattr(current_collector, f"{param}_range")[0] for param in TAPE_RANGE_SLIDER_PARAMETERS]
        max_val = [getattr(current_collector, f"{param}_range")[1] for param in TAPE_RANGE_SLIDER_PARAMETERS]
        range_marks_list = [getattr(current_collector, f"{param}_marks") for param in TAPE_RANGE_SLIDER_PARAMETERS]
        return parameter_list, start_list, end_list, min_val, max_val, range_marks_list

    triggered_id = ctx.triggered_id
    cell = cache.get(cell_data['cache_key'])

    # get the cathode current collector from the cell
    current_collector = cell

    # Check if the current collector is a TablessCurrentCollector. If not, return no_update
    if type(current_collector) != TablessCurrentCollector:
        return (
            no_update,
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
        )

    # If the cell store is triggered, get the current collector from the cell
    if triggered_id == 'cell_store':
        
        # generate the parameter lists
        value_list, min_values, max_values, marks_list = generate_parameters(current_collector)

        # generate the range slider values
        range_value_list, start_list, end_list, min_val, max_val, range_marks_list = generate_rangeslider_values(current_collector)

        return (
            no_update,
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
            range_value_list,
            start_list,
            end_list,
            min_val,
            max_val,
            range_marks_list
        )
        
    # Handle slider/input updates
    elif isinstance(triggered_id, dict) and 'property' in triggered_id:

        # determine which property was triggered
        property = triggered_id['property']
        
        # Handle range slider properties
        if property in TAPE_RANGE_SLIDER_PARAMETERS:

            range_property_index = TAPE_RANGE_SLIDER_PARAMETERS.index(property)
            
            if triggered_id['subtype'] == 'rangeslider':
                # Range slider was moved
                value = rangeslider_values[range_property_index]
            elif triggered_id['subtype'] == 'input_start':
                # Start input was changed
                current_value = getattr(current_collector, property)
                value = (input_start_values[range_property_index], current_value[1])
            elif triggered_id['subtype'] == 'input_end':
                # End input was changed
                current_value = getattr(current_collector, property)
                value = (current_value[0], input_end_values[range_property_index])
            
            # Set the property as a tuple
            setattr(current_collector, property, value)
            
        # Handle regular slider/input properties  
        elif property in TABLESS_PARAMETER_LIST:
            property_index = TABLESS_PARAMETER_LIST.index(property)
            value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]
            setattr(current_collector, property, value)

        # Validate dependent properties for regular parameters only
        for param in TABLESS_SETTABLE_PARAMETERS:
            if param != property:  # Skip the updated property
                param_range = getattr(current_collector, f"{param}_range")
                param_value = getattr(current_collector, param)
                if param_value < param_range[0]:
                    setattr(current_collector, param, param_range[0])
                elif param_value > param_range[1]:
                    print(param)
                    setattr(current_collector, param, param_range[1])

        value_list, min_values, max_values, marks_list = generate_parameters(current_collector)
        range_value_list, start_list, end_list, min_val, max_val, range_marks_list = generate_rangeslider_values(current_collector)

        # update the cell data with the new current collector
        cell = current_collector

        # make the new key and store in cache
        cell_data['cache_key'] = str(uuid4())
        cache.set(cell_data['cache_key'], cell)

        # return the updated values
        return (
            {'cache_key': cell_data['cache_key']},
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
            range_value_list,
            start_list,
            end_list, 
            min_val,
            max_val,
            range_marks_list
        )
    
    elif isinstance(triggered_id, dict) and 'action' in triggered_id:

        # Handle flip actions
        if triggered_id['action'] == 'flip_x':
            current_collector.flip(axis='x')
        elif triggered_id['action'] == 'flip_y':
            current_collector.flip(axis='y')
            
        # update the cell data with the new current collector
        cell = current_collector

        # make the new key and store in cache
        cell_data['cache_key'] = str(uuid4())
        cache.set(cell_data['cache_key'], cell)

        return (
            {'cache_key': cell_data['cache_key']},
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TABLESS_PARAMETER_LIST),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
        )


@callback(
    [
        Output('cell_store', 'data', allow_duplicate=True),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'marks'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'min'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'max'),
        Output({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'marks'),
    ],
    [
        Input('cell_store', 'data'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'slider'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'action': 'flip_x'}, 'n_clicks'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'action': 'flip_y'}, 'n_clicks'),
        # Add range slider inputs
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'rangeslider'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_start'}, 'value'),
        Input({'electrode': 'cathode', 'object': 'tabbed_current_collector', 'property': ALL, 'subtype': 'input_end'}, 'value'),
    ],
    prevent_initial_call=True
)
def update_tabbed_current_collector(
    cell_data,
    input_values,
    slider_values,
    flip_x,
    flip_y,
    rangeslider_values,
    input_start_values,
    input_end_values
):
    
    def generate_parameters(current_collector):
        """Helper function to generate parameter lists for the material."""
        parameter_list = [getattr(current_collector, param) for param in TABBED_PARAMETER_LIST]
        min_values = [getattr(current_collector, f"{param}_range")[0] for param in TABBED_PARAMETER_LIST]
        max_values = [getattr(current_collector, f"{param}_range")[1] for param in TABBED_PARAMETER_LIST]
        marks_list = [getattr(current_collector, f"{param}_marks") for param in TABBED_PARAMETER_LIST]
        return parameter_list, min_values, max_values, marks_list
    
    def generate_rangeslider_values(current_collector):
        """Generate the values for the range slider."""
        parameter_list = [getattr(current_collector, param) for param in TAPE_RANGE_SLIDER_PARAMETERS]
        start_list = [p[0] for p in parameter_list]
        end_list = [p[1] for p in parameter_list]
        min_val = [getattr(current_collector, f"{param}_range")[0] for param in TAPE_RANGE_SLIDER_PARAMETERS]
        max_val = [getattr(current_collector, f"{param}_range")[1] for param in TAPE_RANGE_SLIDER_PARAMETERS]
        range_marks_list = [getattr(current_collector, f"{param}_marks") for param in TAPE_RANGE_SLIDER_PARAMETERS]
        return parameter_list, start_list, end_list, min_val, max_val, range_marks_list

    triggered_id = ctx.triggered_id
    cell = cache.get(cell_data['cache_key'])

    # get the cathode current collector from the cell
    current_collector = cell

    # Check if the current collector is a TablessCurrentCollector. If not, return no_update
    if type(current_collector) != TabWeldedCurrentCollector:

        return (
            no_update,
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
        )

    # If the cell store is triggered, get the current collector from the cell
    if triggered_id == 'cell_store':
        
        # generate the parameter lists
        value_list, min_values, max_values, marks_list = generate_parameters(current_collector)

        # generate the range slider values
        range_value_list, start_list, end_list, min_val, max_val, range_marks_list = generate_rangeslider_values(current_collector)

        return (
            no_update,
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
            range_value_list,
            start_list,
            end_list,
            min_val,
            max_val,
            range_marks_list
        )
        
    # Handle slider/input updates
    elif isinstance(triggered_id, dict) and 'property' in triggered_id:

        # determine which property was triggered
        property = triggered_id['property']
        
        # Handle range slider properties
        if property in TAPE_RANGE_SLIDER_PARAMETERS:

            range_property_index = TAPE_RANGE_SLIDER_PARAMETERS.index(property)
            
            if triggered_id['subtype'] == 'rangeslider':
                # Range slider was moved
                value = rangeslider_values[range_property_index]
            elif triggered_id['subtype'] == 'input_start':
                # Start input was changed
                current_value = getattr(current_collector, property)
                value = (input_start_values[range_property_index], current_value[1])
            elif triggered_id['subtype'] == 'input_end':
                # End input was changed
                current_value = getattr(current_collector, property)
                value = (current_value[0], input_end_values[range_property_index])
            
            # Set the property as a tuple
            setattr(current_collector, property, value)
            
        # Handle regular slider/input properties  
        elif property in TABBED_PARAMETER_LIST:
            property_index = TABBED_PARAMETER_LIST.index(property)
            value = slider_values[property_index] if triggered_id['subtype'] == 'slider' else input_values[property_index]
            setattr(current_collector, property, value)

        # Validate dependent properties for regular parameters only
        for param in TABBED_SETTABLE_PARAMETERS:
            if param != property:  # Skip the updated property
                param_range = getattr(current_collector, f"{param}_range")
                param_value = getattr(current_collector, param)
                if param_value < param_range[0]:
                    setattr(current_collector, param, param_range[0])
                elif param_value > param_range[1]:
                    print(param)
                    setattr(current_collector, param, param_range[1])

        value_list, min_values, max_values, marks_list = generate_parameters(current_collector)
        range_value_list, start_list, end_list, min_val, max_val, range_marks_list = generate_rangeslider_values(current_collector)

        # update the cell data with the new current collector
        cell = current_collector

        # make the new key and store in cache
        cell_data['cache_key'] = str(uuid4())
        cache.set(cell_data['cache_key'], cell)

        # return the updated values
        return (
            {'cache_key': cell_data['cache_key']},
            value_list,
            value_list,
            min_values,
            max_values,
            min_values,
            max_values,
            marks_list,
            range_value_list,
            start_list,
            end_list, 
            min_val,
            max_val,
            range_marks_list
        )
    
    elif isinstance(triggered_id, dict) and 'action' in triggered_id:

        # Handle flip actions
        if triggered_id['action'] == 'flip_x':
            current_collector.flip(axis='x')
        elif triggered_id['action'] == 'flip_y':
            current_collector.flip(axis='y')
            
        # update the cell data with the new current collector
        cell = current_collector

        # make the new key and store in cache
        cell_data['cache_key'] = str(uuid4())
        cache.set(cell_data['cache_key'], cell)

        return (
            {'cache_key': cell_data['cache_key']},
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TABBED_PARAMETER_LIST),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
            [no_update] * len(TAPE_RANGE_SLIDER_PARAMETERS),
        )


@callback(
    [
        Output('cathode_a_side_plot', 'figure'),
        Output('cathode_b_side_plot', 'figure'),
        Output('cathode_top_down_plot', 'figure'),
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
    # get the cell from the cache
    cell = cache.get(cell_data['cache_key'])

    # get the current collector from the cell
    current_collector = cell

    # get the plots from the current collector
    a_side_plot = current_collector.get_a_side_view(with_dimensions=False, title='A-Side Current Collector View')
    b_side_plot = current_collector.get_b_side_view(with_dimensions=False, title='B-Side Current Collector View')
    top_down_plot = current_collector.get_top_down_view(with_dimensions=False, title='Top-Down Current Collector View')

    # return the plots
    return a_side_plot, b_side_plot, top_down_plot

