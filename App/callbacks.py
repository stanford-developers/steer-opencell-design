import dash as ds
from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive

HEADER_STYLE = {'textAlign': 'left', 'padding-left': '0px'}
DIV_STYLE = {'padding-left': '20px', 'width': '50%'}
DROPDOWN_STYLE = {'width': '70%'}

@ds.callback(
    [ds.Output('internal_structure_dropdown', 'options'), ds.Output('internal_structure_dropdown', 'value')],
    ds.Input('form_factor_dropdown', 'value')
)
def update_internal_structure_options(form_factor):
    """
    Update the options for the internal structure dropdown based on the selected form factor.

    :param form_factor: The selected form factor.
    :return: The options for the internal structure dropdown.
    """
    if form_factor == 'cylindrical':
        return [{'label': 'Wound', 'value': 'wound'}], 'wound'
    elif form_factor == 'prismatic':
        return [{'label': 'Stacked', 'value': 'stacked'}], 'stacked'
    elif form_factor == 'pouch':
        return [{'label': 'Stacked', 'value': 'stacked'}], 'stacked'
    else:
        return [], None


@ds.callback(
    ds.Output('num_electrode_assemblies', 'children'),
    ds.Input('form_factor_dropdown', 'value')
)
def update_num_electrode_assemblies_max(form_factor):
    """
    Update the maximum value for the number of electrode assemblies input based on the selected form factor.

    :param form_factor: The selected form factor.
    :return: The maximum value for the number of electrode assemblies input.
    """
    if form_factor == 'cylindrical':
        return None
    elif form_factor == 'prismatic':
        return [ds.html.H3('Number of electrode assemblies', style=HEADER_STYLE),
                ds.dcc.Input(
                id='num_electrode_assemblies',
                type='number',
                min=1,
                max=6,
                value=1,
                style=DROPDOWN_STYLE)]
    elif form_factor == 'pouch':
        return [ds.html.H3('Number of electrode assemblies', style=HEADER_STYLE),
                ds.dcc.Input(
                id='num_electrode_assemblies',
                type='number',
                min=1,
                max=6,
                value=1,
                style=DROPDOWN_STYLE)]
    else:
        return None
    

@ds.callback(
    ds.Output('cathode_active_materials_list', 'data'),
    ds.Input('form_factor_dropdown', 'value')
)
def fetch_and_store_cathode_active_materials_list(_):
    """
    Fetch and store the list of active materials for the cathode based on the selected form factor.

    :param form_factor: The selected form factor.
    :return: The list of active materials for the cathode.
    """
    active_materials = CathodeMaterial.get_available_materials()
    return active_materials


@ds.callback(
    ds.Output('anode_active_materials_list', 'data'),
    ds.Input('form_factor_dropdown', 'value')
)
def fetch_and_store_anode_active_materials_list(_):
    """
    Fetch and store the list of active materials for the anode based on the selected form factor.

    :param form_factor: The selected form factor.
    :return: The list of active materials for the anode.
    """
    active_materials = AnodeMaterial.get_available_materials()
    return active_materials


@ds.callback(
    ds.Output('active_materials_list', 'children'),
    ds.Input('add_active_materials', 'n_clicks'),
    ds.Input('cathode_active_materials_list', 'data'),
    ds.State('active_materials_list', 'children')
)
def update_cathode_active_materials_list(n_clicks, active_materials, current_children):
    """
    Fetch and display the list of active materials as a dropdown menu with a slider and an input box.

    :param _: Input value (not used in this case).
    :return: A Div containing a dropdown menu, a slider, and an input box.
    """
    drop_down = ds.dcc.Dropdown(
                id='active_materials_dropdown',
                options=[{'label': material, 'value': material} for material in active_materials],
                placeholder='Select an active material',
                style={'width': '100%', 'margin-right': '10px'})
    
    slider_header = ds.html.P("Weight Percentage:", style={'margin-bottom': '5px', 'margin-left': '20px'}) if n_clicks == 0 else ds.html.Br()
    
    slider = ds.dcc.Slider(id='active_materials_slider',
                           min=0,
                           max=100,
                           step=1,
                           value=50,  # Default value
                           marks={i: str(i) for i in range(0, 101, 10)},  # Marks every 10
                           tooltip={"placement": "bottom", "always_visible": True})
    
    slider_input = ds.dcc.Input(id='active_materials_input',
                                type='number',
                                min=0,
                                max=100,
                                step=1,
                                value=50,  # Default value
                                style={'width': '20%','margin-left': '10px', 'margin-bottom': '15px'})


    new_component = ds.html.Div([
            drop_down,
            ds.html.Div([slider_header, slider], style={'margin-bottom': '5px', 'align-items': 'center', 'width': '100%'}),
            slider_input
        ], style={'display': 'flex', 'align-items': 'center', 'margin-bottom': '10px'})

    # Append the new component to the existing children
    if current_children is None:
        current_children = []
    current_children.append(new_component)

    return current_children
    
    

@ds.callback(
    [ds.Output('active_materials_slider', 'value'),
     ds.Output('active_materials_input', 'value')],
    [ds.Input('active_materials_slider', 'value'),
     ds.Input('active_materials_input', 'value')]
)
def sync_slider_and_input(slider_value, input_value):
    """
    Synchronize the slider and input box values.

    :param slider_value: The value from the slider.
    :param input_value: The value from the input box.
    :return: The synchronized values for both components.
    """
    ctx = ds.callback_context

    # Determine which input triggered the callback
    if not ctx.triggered:
        return slider_value, slider_value
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'active_materials_slider':
        return slider_value, slider_value
    elif trigger_id == 'active_materials_input':
        return input_value, input_value

    return slider_value, input_value