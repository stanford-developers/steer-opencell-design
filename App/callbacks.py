import dash as ds
import pickle
import base64
import ast
from styles import *
from custom_components import CathodeMaterialSelector, AnodeMaterialSelector, SliderWithTextInput, BinderSelector, ConductiveAdditiveSelector
from layouts import *

from SteerEnergyStorage.Materials.ElectrodeMaterials import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from SteerEnergyStorage.Formulations.ElectrodeFormulations import ElectrodeFormulation
from SteerEnergyStorage.Materials.Separators import Separator
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector, NotchedCurrentCollector, TabWeldedCurrentCollector, TablessCurrentCollector
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Materials.other import Terminal
from SteerEnergyStorage.Constructions.Containers import CylindricalCase, CylindricalShell
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.ElectrodeAssemblies import CylindricalJellyRoll
from SteerEnergyStorage.Constructions.Cells import CylindricalCell


@ds.callback(
    [ds.Output('cathode_mechanicals', 'style'),
     ds.Output('anode_mechanicals', 'style'),
     ds.Output('encapsulation', 'style'),
     ds.Output('cathode_design', 'style'),
     ds.Output('anode_design', 'style'),
     ds.Output('separator_electrolyte_design', 'style')],
     ds.Output('electrodes', 'style'),
    ds.Input('tabs-container', 'value'),
    prevent_initial_call=True
)
def show_tab_content(active_tab):

    styles = {'display': 'none'}
    active_style = {'display': 'block'}

    return [
        active_style if active_tab == 'cathode_mechanicals' else styles,
        active_style if active_tab == 'anode_mechanicals' else styles,
        active_style if active_tab == 'encapsulation' else styles,
        active_style if active_tab == 'cathode_design' else styles,
        active_style if active_tab == 'anode_design' else styles,
        active_style if active_tab == 'separator_electrolyte_design' else styles,
        active_style if active_tab == 'electrodes' else styles,
    ]


@ds.callback(
    [ds.Output('internal_structure_dropdown', 'options'), 
     ds.Output('internal_structure_dropdown', 'value'),
     ds.Output('num_electrode_assemblies', 'value'),
     ds.Output('num_electrode_assemblies', 'options')],
    ds.Input('form_factor_dropdown', 'value'),
    prevent_initial_call=True
)
def update_internal_structure_options(form_factor_value):
    """
    Update the options for the internal structure dropdown based on the selected form factor.

    :param form_factor: The selected form factor.
    :return: The options for the internal structure dropdown.
    """
    if form_factor_value == 'cylindrical':
        assembly_options = [{'label': (str(1) + ' Electrode Assembly'), 'value': 1}]
        return [{'label': 'Wound', 'value': 'wound'}], 'wound', 1, assembly_options
    
    elif form_factor_value == 'prismatic':
        assembly_options = [{'label': (str(1) + ' Electrode Assembly'), 'value': 1}] + [{'label': str(i) + ' Electrode Assemblies', 'value': i} for i in range(2, 7)]
        return [{'label': 'Stacked', 'value': 'stacked'}], 'stacked', 1, assembly_options
    
    elif form_factor_value == 'pouch':
        assembly_options = [{'label': (str(1) + ' Electrode Assembly'), 'value': 1}] + [{'label': str(i) + ' Electrode Assemblies', 'value': i} for i in range(2, 7)]
        return [{'label': 'Stacked', 'value': 'stacked'}], 'stacked', 1, assembly_options

    else:
        return [], None, 1, 1
    

@ds.callback(
    [ds.Output(component_id={'type': 'store', 'electrode': 'cathode'}, component_property='data'),
     ds.Output(component_id={'type': 'store', 'electrode': 'anode'}, component_property='data')],
    ds.Input('app-load-trigger', 'data')
)
def fetch_and_store_active_materials(_):
    """
    Fetch and store the list of active materials for the specified electrode.

    :param _: Input value (not used).
    :param electrode: The electrode type (e.g., 'cathode' or 'anode') from the pattern-matching ID.
    :return: The list of active materials for the specified electrode.
    """
    active_materials_cathode = CathodeMaterial.get_available_materials()
    active_materials_anode = AnodeMaterial.get_available_materials()
    return active_materials_cathode, active_materials_anode


@ds.callback(
    [ds.Output(component_id={'type': 'store', 'object': 'currrent_collector', 'type': 'materials'}, component_property='data')],
    ds.Input('app-load-trigger', 'data')
)
def fetch_and_store_current_collector_materials(_):
    """
    Fetch and store the list of current collector materials.

    :param _: Input value (not used).
    :return: The list of current collector materials.
    """
    current_collector_materials = CurrentCollector.get_available_materials()
    return [current_collector_materials]


@ds.callback(
    ds.Output(component_id={'type': 'materials_selector', 'electrode': ds.MATCH, 'material': ds.MATCH}, component_property='children'),
    ds.Input(component_id={'type': 'button', 'action': ds.ALL, 'electrode': ds.MATCH, 'material': ds.MATCH}, component_property='n_clicks'),
    [ds.State(component_id={'type': 'store', 'electrode': ds.MATCH}, component_property='data'),
     ds.State(component_id={'type': 'materials_selector', 'electrode': ds.MATCH, 'material': ds.MATCH}, component_property='children')],
    prevent_initial_call=True
)
def update_material_input(n_clicks, active_materials, current_children):
    """
    Add or remove active material components based on button clicks.

    :param n_clicks: The number of clicks for the add/remove buttons.
    :param active_materials: The list of active materials for the specified electrode.
    :param current_children: The current children of the materials selector.
    :return: The updated children of the materials selector.
    """
    ctx = ds.callback_context
    trigger_id = ast.literal_eval(ctx.triggered[0]['prop_id'].split('.')[0])

    action = trigger_id['action']
    electrode = trigger_id['electrode']
    material = trigger_id['material']
    n_items = len(current_children) if current_children else 0

    id = {'type': material, 'index': n_items, 'electrode': electrode}

    with_slider_titles = False if n_items > 0 else True

    if action == 'remove' and n_items > 0:
        current_children.pop()
        return current_children
    elif action == 'remove' and n_items == 0:
        return current_children

    if material == 'active_material' and electrode == 'cathode':
        weight_default = 100 if n_items == 0 else 0
        new_component = CathodeMaterialSelector(id=id, materials=active_materials, with_slider_titles=with_slider_titles, weight_default=weight_default).render()
    elif material == 'active_material' and electrode == 'anode':
        weight_default = 100 if n_items == 0 else 0
        new_component = AnodeMaterialSelector(id=id, materials=active_materials, with_slider_titles=with_slider_titles, weight_default=weight_default).render()
    elif material == 'binder':
        new_component = BinderSelector(id, with_slider_titles).render()
    elif material == 'conductive_additive':
        new_component = ConductiveAdditiveSelector(id, with_slider_titles).render()

    if not current_children:
        current_children = []

    current_children.append(new_component)
    
    return current_children
    
    
@ds.callback(
    [ds.Output({'type': ds.MATCH, 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': ds.MATCH}, 'value'),
     ds.Output({'type': ds.MATCH, 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'input', 'property': ds.MATCH}, 'value')],
    [ds.Input({'type': ds.MATCH, 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': ds.MATCH}, 'drag_value'),
     ds.Input({'type': ds.MATCH, 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'input', 'property': ds.MATCH}, 'value')],
     ds.State({'type': ds.MATCH, 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': ds.MATCH}, 'value'),
     Prevent_initial_call=True
)
def sync_slider_and_input_material_selectors(slider_value, input_value, default_value):
    """
    Synchronize the slider and input box values.

    :param slider_value: The value from the slider.
    :param input_value: The value from the input box.
    :return: The synchronized values for both components.
    """
    ctx = ds.callback_context

    if not ctx.triggered:
        return default_value, default_value

    trigger_id = ast.literal_eval(ctx.triggered[0]['prop_id'].split('.')[0])

    if trigger_id['subtype'] == 'slider':
        return slider_value, slider_value
    elif trigger_id['subtype'] == 'input':
        return input_value, input_value

    return slider_value, input_value


@ds.callback(
    ds.Output({'type': 'active_material', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'store', 'property': 'object'}, 'data'),
    [ds.Input({'type': 'active_material', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'text_input', 'property': 'name'}, 'value'),
     ds.Input({'type': 'active_material', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'specific_cost'}, 'value'),
     ds.Input({'type': 'active_material', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'density'}, 'value'),
     ds.Input({'type': 'active_material', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'reversible_capacity'}, 'value'),
     ds.Input({'type': 'active_material', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'irreversible_capacity'}, 'value'),
     ds.Input({'type': 'active_material', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'weight'}, 'value')],
     prevent_initial_call=True
)
def make_active_material(material_name, specific_cost, density, reversible_capacity, irreversible_capacity, weight_percent):
    """
    Create an active material object using the inputs from the sliders and text box.

    :param material_name: Name of the material from the text input.
    :param specific_cost: Specific cost value from the slider.
    :param density: Density value from the slider.
    :param reversible_capacity: Reversible capacity scaling from the slider.
    :param irreversible_capacity: Irreversible capacity scaling from the slider.
    :param weight_percent: Weight percentage from the slider.
    """
    ctx = ds.callback_context
    trigger_id = ast.literal_eval(ctx.triggered[0]['prop_id'].split('.')[0])
    electrode = trigger_id['electrode']

    if material_name == None:
        return {}

    if electrode == 'cathode':
        material = CathodeMaterial(name=material_name,
            specific_cost=specific_cost,
            density=density,
            reversible_capacity_scaling=reversible_capacity,
            irreversible_capacity_scaling=irreversible_capacity
        )
    elif electrode == 'anode':
        material = AnodeMaterial(
            name=material_name,
            specific_cost=specific_cost,
            density=density,
            reversible_capacity_scaling=reversible_capacity,
            irreversible_capacity_scaling=irreversible_capacity
        )

    pickled_material = base64.b64encode(pickle.dumps(material)).decode('utf-8')
    store_data = {pickled_material: weight_percent}
    return store_data


@ds.callback(
    ds.Output({'type': 'binder', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'store', 'property': 'object'}, 'data'),
    [ds.Input({'type': 'binder', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'text_input', 'property': 'name'}, 'value'),
     ds.Input({'type': 'binder', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'specific_cost'}, 'value'),
     ds.Input({'type': 'binder', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'density'}, 'value'),
     ds.Input({'type': 'binder', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'weight'}, 'value')],
     prevent_initial_call=True
)
def make_binder(material_name, specific_cost, density, weight_percent):
    """
    Create a binder object using the inputs from the sliders and text box.

    :param material_name: Name of the material from the text input.
    :param specific_cost: Specific cost value from the slider.
    :param density: Density value from the slider.
    :param weight_percent: Weight percentage from the slider.
    """
    material = Binder(specific_cost=specific_cost, density=density, name=material_name)
    pickled_material = base64.b64encode(pickle.dumps(material)).decode('utf-8')
    store_data = {pickled_material: weight_percent}
    return store_data


@ds.callback(
    ds.Output({'type': 'conductive_additive', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'store', 'property': 'object'}, 'data'),
    [ds.Input({'type': 'conductive_additive', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'text_input', 'property': 'name'}, 'value'),
     ds.Input({'type': 'conductive_additive', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'specific_cost'}, 'value'),
     ds.Input({'type': 'conductive_additive', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'density'}, 'value'),
     ds.Input({'type': 'conductive_additive', 'electrode': ds.MATCH, 'index': ds.MATCH, 'subtype': 'slider', 'property': 'weight'}, 'value')],
     prevent_initial_call=True
)
def make_conductive_additive(material_name, specific_cost, density, weight_percent):
    """
    Create a conductive additive object using the inputs from the sliders and text box.

    :param material_name: Name of the material from the text input.
    :param specific_cost: Specific cost value from the slider.
    :param density: Density value from the slider.
    :param weight_percent: Weight percentage from the slider.
    """
    material = ConductiveAdditive(specific_cost=specific_cost, density=density, name=material_name)
    pickled_material = base64.b64encode(pickle.dumps(material)).decode('utf-8')
    store_data = {pickled_material: weight_percent}
    return store_data


@ds.callback(
    [ds.Output({'type': 'formulation_properties_text', 'electrode': ds.MATCH}, 'children'),
     ds.Output({'type': 'store', 'electrode': ds.MATCH, 'object': 'formulation'}, 'data')],
    [ds.Input({'type': ds.ALL, 'index': ds.ALL, 'electrode': ds.MATCH, 'subtype': 'store', 'property': 'object'}, 'data')],
    [ds.State({'type': 'formulation_properties_text', 'electrode': ds.MATCH}, 'children')],
    prevent_initial_call=True
)
def update_formulation(data_list, current_children):
    """
    Update the formulation properties text and store the formulation data.

    :param data_list: List of data from the stores.
    :return: The updated formulation properties text and store data.
    """
    if data_list == [] or data_list == [{}]:
        return '-', {}
    
    unpickled_data = [{pickle.loads(base64.b64decode(key)): value for key, value in item.items()} for item in data_list]
    
    active_material_dict = {key: value for d in unpickled_data for key, value in d.items() if type(key) == CathodeMaterial or type(key) == AnodeMaterial}
    binder_dict = {key: value for d in unpickled_data for key, value in d.items() if type(key) == Binder}
    conductive_additive_dict = {key: value for d in unpickled_data for key, value in d.items() if type(key) == ConductiveAdditive}

    try:
        formulation = ElectrodeFormulation(
            active_materials=active_material_dict,
            binders=binder_dict,
            conductive_additives=conductive_additive_dict
        )
    except ValueError as e:
        message = f"Error: {e}"
        return message, {}
    
    pickled_formulation = base64.b64encode(pickle.dumps(formulation)).decode('utf-8')

    formulation_text = ds.html.Div([
        ds.html.Br(),
        ds.html.P("Formulation created successfully."),
        ds.html.Br(),
        ds.html.P(f"Formulation specific cost: {formulation.specific_cost} $/kg")
    ], style={'line-height': '0.5'})

    return formulation_text, {'formulation': pickled_formulation}


@ds.callback(
    [ds.Output({'type': 'operation', 'subtype': 'range_slider', 'property': ds.MATCH}, 'value'),
     ds.Output({'type': 'operation', 'subtype': 'input', 'property': ds.MATCH, 'select_value': 'min'}, 'value'),
     ds.Output({'type': 'operation', 'subtype': 'input', 'property': ds.MATCH, 'select_value': 'max'}, 'value')],
    [ds.Input({'type': 'operation', 'subtype': 'range_slider', 'property': ds.MATCH}, 'drag_value'),
     ds.Input({'type': 'operation', 'subtype': 'input', 'property': ds.MATCH, 'select_value': 'min'}, 'value'),
     ds.Input({'type': 'operation', 'subtype': 'input', 'property': ds.MATCH, 'select_value': 'max'}, 'value')],
    prevent_initial_call=True
)
def sync_range_slider_and_inputs(slider_value, input_min, input_max):
    """
    Callback to update the values on the voltage range slider
    
    :param slider_value: A tuple of the two values of the slider
    :param input_min: The first input box
    :param input_max: The second input box
    """
    ctx = ds.callback_context
    triggered_id = ctx.triggered_id

    if triggered_id['subtype'] == 'range_slider':
        return slider_value, min(slider_value), max(slider_value)
    elif triggered_id['subtype'] == 'input' and triggered_id['select_value'] == 'min':
        return [input_min, input_max], min([input_min, input_max]), max([input_min, input_max])
    elif triggered_id['subtype'] == 'input' and triggered_id['select_value'] == 'max':
        return [input_min, input_max], min([input_min, input_max]), max([input_min, input_max])


@ds.callback(
        [ds.Output({'type': ds.MATCH, 'subtype': 'slider', 'property': ds.MATCH}, 'value'),
         ds.Output({'type': ds.MATCH, 'subtype': 'input', 'property': ds.MATCH}, 'value')],
        [ds.Input({'type': ds.MATCH, 'subtype': 'slider', 'property': ds.MATCH}, 'drag_value'),
         ds.Input({'type': ds.MATCH, 'subtype': 'input', 'property': ds.MATCH}, 'value')],
        [ds.State({'type': ds.MATCH, 'subtype': 'slider', 'property': ds.MATCH}, 'drag_value'),
         ds.State({'type': ds.MATCH, 'subtype': 'input', 'property': ds.MATCH}, 'value')],
         prevent_initial_call=True
)
def sync_generic_sliders(slider_val, input_val, default_slider_val, default_input_val):
    """
    Generic function to sync sliders with this ID format

    :parameter slider_val: The drag value of the slider to by synced
    :parameter input_val: The value of the inpout box being synced
    """
    ctx = ds.callback_context
    triggered_id = ctx.triggered_id
    component = triggered_id['subtype']

    if component == 'slider':
        return slider_val, slider_val
    elif component == 'input':
        return input_val, input_val
    else:
        return default_slider_val, default_input_val


@ds.callback(
    ds.Output({'type': 'div', 'object': 'n_stacks'}, 'children'),
    [ds.Input('form_factor_dropdown', 'value'),
     ds.Input('internal_structure_dropdown', 'value')],
    prevent_initial_call=True
)
def update_stack_slider(form_factor, internal_structure):
    """
    Show the number of stacks slider based on the selected form factor and internal structure.

    :param form_factor: The selected form factor.
    :param internal_structure: The selected internal structure.
    :return: The updated number of stacks slider.
    """
    if form_factor == 'pouch' and internal_structure == 'stacked':

        return [SliderWithTextInput(id={'type': 'electrodes'}, 
                                    min_val=0, 
                                    max_val=50, 
                                    default_val=20, 
                                    step=1, 
                                    mark_interval=5, 
                                    property_name='n_stacks',
                                    div_width='80%',
                                    title="Number of electrode stacks").render()]
    
    else:
        return []
    

@ds.callback(
    [ds.Output({'type': 'separator_message_text'}, 'children'), 
     ds.Output({'type': 'store', 'component': 'separator'}, 'data')],
    [ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': 'separator_thickness'}, 'value'),
     ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': 'separator_density'}, 'value'),
     ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': 'separator_areal_cost'}, 'value'), 
     ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': 'separator_porosity'}, 'value'),
     ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': 'separator_fold_length'}, 'value'),
     ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': 'separator_width'}, 'value')],
     prevent_initial_call=True
)
def make_separator(thickness, density, areal_cost, porosity, fold_length, width):
    """
    Create a separator object using the inputs from the sliders and text box.

    :param thickness: Thickness of the separator.
    :param density: Density of the separator.
    :param areal_cost: Areal cost of the separator.
    :param porosity: Porosity of the separator.
    :param fold_length: Fold length of the separator.
    :param width: Width of the separator.
    """
    try:
        separator = Separator(thickness=thickness, density=density, areal_cost=areal_cost, porosity=porosity, fold_length=fold_length, width=width)
    except ValueError as e:
        message = f"Error: {e}"
        return message, {}
    
    pickled_separator = base64.b64encode(pickle.dumps(separator)).decode('utf-8')

    separator_text = ds.html.Div([
        ds.html.Br(),
        ds.html.P("\u00A0"),
        ds.html.Br(),
    ], style={'line-height': '0.5'})

    return separator_text, {'separator': pickled_separator}


@ds.callback(
    [ds.Output({'type': 'mechanicals', 'object': 'current_collector', 'electrode': 'cathode', 'feature': 'design'}, 'options'),
     ds.Output({'type': 'mechanicals', 'object': 'current_collector', 'electrode': 'anode', 'feature': 'design'}, 'options'),
     ds.Output({'type': 'mechanicals', 'object': 'current_collector', 'electrode': 'cathode', 'feature': 'design'}, 'value'),
     ds.Output({'type': 'mechanicals', 'object': 'current_collector', 'electrode': 'anode', 'feature': 'design'}, 'value')],
    [ds.Input('internal_structure_dropdown', 'value')],
    prevent_initial_call=True
)
def update_current_collector_design_options(internal_structure):
    """
    Update the current collector design options based on the selected internal structure.

    :param internal_structure: The selected internal structure.
    :return: The updated current collector design options for both electrodes.
    """
    if internal_structure == 'wound':
        options = [{'label': 'Tabless', 'value': 'tabless'}, 
                   {'label': 'Notched', 'value': 'notched'}, 
                   {'label': 'Tab Welded', 'value': 'tab_welded'}]
        return options, options, 'tabless', 'tabless'
    elif internal_structure == 'stacked':
        options = [{'label': 'Punched', 'value': 'punched'}]
        return options, options, 'punched', 'punched'
    else:
        return [], [], None, None
    

@ds.callback(
    [ds.Output({'type': 'electrolyte_message_text'}, 'children'), 
     ds.Output({'type': 'store', 'component': 'electrolyte'}, 'data')],
    [ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': 'electrolyte_specific_cost'}, 'value'),
     ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': 'electrolyte_density'}, 'value')],
     prevent_initial_call=True
)
def make_separator(specific_cost, density):
    """
    Create a separator object using the inputs from the sliders and text box.

    :param thickness: Thickness of the separator.
    :param density: Density of the separator.
    :param areal_cost: Areal cost of the separator.
    :param porosity: Porosity of the separator.
    :param fold_length: Fold length of the separator.
    :param width: Width of the separator.
    """
    try:
        electrolyte = Electrolyte(specific_cost=specific_cost, density=density)
    except ValueError as e:
        message = f"Error: {e}"
        return message, {}
    
    pickled_electrolyte = base64.b64encode(pickle.dumps(electrolyte)).decode('utf-8')

    electrolyte_text = ds.html.Div([
        ds.html.Br(),
        ds.html.P("\u00A0"),
        ds.html.Br(),
    ], style={'line-height': '0.5'})

    return electrolyte_text, {'electrolyte': pickled_electrolyte}


@ds.callback(
    ds.Output({'tab': 'mechanicals', 'object': 'current_collector', 'object': 'div', 'electrode': ds.MATCH}, 'children'),
    ds.Input({'type': 'mechanicals', 'object': 'current_collector', 'electrode': ds.MATCH, 'feature': 'design'}, 'value'),
    prevent_initial_call=True
)
def show_current_collector_design_options(design):
    """
    Show the current collector design options based on the selected internal structure.
    """
    ctx = ds.callback_context
    triggered_id = ast.literal_eval(ctx.triggered[0]['prop_id'].split('.')[0])
    electrode = triggered_id['electrode']

    if design == 'notched':
        return [
            ds.html.Br(), 
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 600, 100, 0.01, 10, 'length', 'Length (cm)', div_width='1400px').render(), ds.html.Br(), 
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 40, 12, 0.01, 2, 'width', 'Width  (cm)', div_width='600px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 100, 15, 0.1, 5, 'thickness', 'Thickness  (μm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 5, 1, 0.01, 1, 'tab_width', 'Tab Width (cm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 20, 3, 0.01, 1, 'tab_length', 'Tab Length (cm)', div_width='600px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 20, 3, 0.01, 1, 'tab_spacing', 'Tab Spacing (cm)', div_width='600px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 50, 0, 0.01, 5, 'bare_length', 'Bare Tape (cm)', div_width='600px').render(), ds.html.Br(),
        ]
    
    elif design == 'tabless':
        return [
            ds.html.Br(), 
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 600, 100, 0.01, 10, 'length', 'Length (cm)', div_width='1400px').render(), ds.html.Br(), 
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 40, 12, 0.01, 2, 'width', 'Width  (cm)', div_width='600px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 100, 15, 0.1, 5, 'thickness', 'Thickness  (μm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 5, 1, 0.01, 1, 'tab_width', 'Tab Width (cm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 50, 0, 0.01, 5, 'bare_length', 'Bare Tape (cm)', div_width='600px').render(), ds.html.Br(),
        ]

    elif design == 'tab_welded':
        return [
            ds.html.P("Tab welded current collector selected for " + electrode),
            ds.html.Br(),
            ds.html.P("Additional parameters for tab welded current collector can be added here.")
        ]
    
    elif design == 'punched':
        return [
            ds.html.P("Punched current collector selected for " + electrode),
            ds.html.Br(),
            ds.html.P("Additional parameters for punched current collector can be added here.")
        ]


@ds.callback(
    [ds.Output({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'slider', 'property': 'density'}, 'value'),
     ds.Output({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'input', 'property': 'density'}, 'value'),
     ds.Output({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'slider', 'property': 'specific_cost'}, 'value'),
     ds.Output({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'input', 'property': 'specific_cost'}, 'value')],
    [ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'text_input', 'property': 'name'}, 'value'),
     ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'slider', 'property': 'density'}, 'drag_value'),
     ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'input', 'property': 'density'}, 'value'),
     ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'slider', 'property': 'specific_cost'}, 'drag_value'),
     ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'input', 'property': 'specific_cost'}, 'value')],
     prevent_initial_call=True
)
def update_current_collector_properties_and_sync(material_formula, density_slider_value, density_input_value, specific_cost_slider_value, specific_cost_input_value):
    """
    Update the current collector properties and synchronize sliders.

    :param material_formula: The selected material formula.
    :param density_slider_value: The current value of the density slider.
    :param specific_cost_slider_value: The current value of the specific cost slider.
    :return: Updated values for density and specific cost sliders.
    """
    ctx = ds.callback_context
    triggered_id = ctx.triggered_id

    if triggered_id and triggered_id['subtype'] == 'text_input':
        if material_formula is None:
            return 4, 4, 15, 15
        current_collector = CurrentCollector(formula=material_formula, length=1, width=1, thickness=1, bare_area=1)
        return current_collector.density, current_collector.density, current_collector.specific_cost, current_collector.specific_cost
    
    elif triggered_id and triggered_id['subtype'] == 'slider':
        return density_slider_value, density_slider_value, specific_cost_slider_value, specific_cost_slider_value
    
    elif triggered_id and triggered_id['subtype'] == 'input':
        return density_input_value, density_input_value, specific_cost_input_value, specific_cost_input_value

    return 4, 4, 15, 15
    

@ds.callback(
    [ds.Output({'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'text_input', 'property': 'name'}, 'options'),
     ds.Output({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'text_input', 'property': 'name'}, 'options'),
     ds.Output({'electrode': 'cathode', 'object': 'current_collector', 'subtype': 'text_input', 'property': 'name'}, 'value'),
     ds.Output({'electrode': 'anode', 'object': 'current_collector', 'subtype': 'text_input', 'property': 'name'}, 'value')],
    [ds.Input({'type': 'store', 'object': 'currrent_collector', 'type': 'materials'}, 'data')],
    prevent_initial_call=True
)
def update_current_collector_material_options(materials):
    """
    Update the current collector options based on the selected internal structure.

    :param materials: The list of current collector materials.
    :return: The updated current collector options for both electrodes.
    """
    if materials == []:
        return []
    
    options = [{'label': material, 'value': material} for material in materials]

    return options, options, options[0]['value'], options[0]['value']


@ds.callback(
        [ds.Output({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'slider'}, 'value'),
         ds.Output({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'input'}, 'value')],
        [ds.Input({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'slider'}, 'drag_value'),
         ds.Input({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'input'}, 'value')],
        [ds.State({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'slider'}, 'drag_value'),
         ds.State({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'input'}, 'value')],
         prevent_initial_call=True
)
def sync_current_collector_and_terminal_sliders(slider_val, input_val, default_slider_val, default_input_val):
    """
    Generic function to sync sliders with this ID format

    :parameter slider_val: The drag value of the slider to by synced
    :parameter input_val: The value of the inpout box being synced
    """
    ctx = ds.callback_context
    triggered_id = ctx.triggered_id
    component = triggered_id['subtype']

    if component == 'slider':
        return slider_val, slider_val
    elif component == 'input':
        return input_val, input_val
    else:
        return default_slider_val, default_input_val
    

@ds.callback(
        [ds.Output({'type': ds.MATCH, 'object': ds.MATCH, 'property': ds.MATCH, 'subtype': 'slider'}, 'value'),
         ds.Output({'type': ds.MATCH, 'object': ds.MATCH, 'property': ds.MATCH, 'subtype': 'input'}, 'value')],
        [ds.Input({'type': ds.MATCH, 'object': ds.MATCH, 'property': ds.MATCH, 'subtype': 'slider'}, 'drag_value'),
         ds.Input({'type': ds.MATCH, 'object': ds.MATCH, 'property': ds.MATCH, 'subtype': 'input'}, 'value')],
        [ds.State({'type': ds.MATCH, 'object': ds.MATCH, 'property': ds.MATCH, 'subtype': 'slider'}, 'drag_value'),
         ds.State({'type': ds.MATCH, 'object': ds.MATCH, 'property': ds.MATCH, 'subtype': 'input'}, 'value')],
         prevent_initial_call=True
)
def sync_encapsulation_sliders(slider_val, input_val, default_slider_val, default_input_val):
    """
    Generic function to sync sliders with this ID format

    :parameter slider_val: The drag value of the slider to by synced
    :parameter input_val: The value of the inpout box being synced
    """
    ctx = ds.callback_context
    triggered_id = ctx.triggered_id
    component = triggered_id['subtype']

    if component == 'slider':
        return slider_val, slider_val
    elif component == 'input':
        return input_val, input_val
    else:
        return default_slider_val, default_input_val
    

@ds.callback(
        [ds.Output({'tab': 'mechanicals', 'object': 'current_collector', 'object': 'message', 'electrode': ds.MATCH}, 'children'),
         ds.Output({'type': 'store', 'electrode': ds.MATCH, 'object': 'current_collector'}, 'data')],
        [ds.Input({'type': ds.ALL, 'object': 'current_collector', 'electrode': ds.MATCH, 'subtype': 'slider', 'property': ds.ALL}, 'drag_value'),
         ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'text_input', 'property': 'name'}, 'value'),
         ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'slider', 'property': 'density'}, 'drag_value'),
         ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'slider', 'property': 'specific_cost'}, 'drag_value')],
         ds.State({'type': 'mechanicals', 'object': 'current_collector', 'electrode': ds.MATCH, 'feature': 'design'}, 'value'),
         prevent_initial_call=True
)
def make_current_collector(properties, material_formula, material_density, material_specific_cost, current_collector_design):
    """
    Create a current collector object using the inputs from the sliders and text box.

    :param properties: Properties of the current collector.
    :param current_collector_design: The selected current collector design.
    """
    ctx = ds.callback_context
    triggered_id = ast.literal_eval(ctx.triggered[0]['prop_id'].split('.')[0])
    electrode = triggered_id['electrode']

    if current_collector_design is None:
        return ["\u00A0"], {}
    
    if properties == []:
            return ["\u00A0"], {}

    if current_collector_design == 'notched':

        try:
            current_collector = NotchedCurrentCollector(
                formula=material_formula,
                length=properties[0],
                width=properties[1],
                thickness=properties[2],
                tab_width=properties[3],
                tab_length=properties[4],
                tab_spacing=properties[5],
                density=material_density,
                specific_cost=material_specific_cost,
                bare_length=properties[6]
            )
        except ValueError as e:
            message = f"Error: {e}"
            return message, {}
        
    elif current_collector_design == 'tabless':

        if properties == []:
            return ["\u00A0"], {}

        try:
            length = properties[0]
            width = properties[1]
            thickness = properties[2]
            tab_width = properties[3]
            bare_length = properties[4]

            current_collector = TablessCurrentCollector(
                formula=material_formula,
                length=length,
                width=width,
                thickness=thickness,
                tab_width=tab_width,
                density=material_density,
                specific_cost=material_specific_cost,
                bare_length=bare_length
            )

        except ValueError as e:
            message = f"Error: {e}"
            return message, {}

    elif current_collector_design == 'tab_welded':
        # Add logic for tab welded design
        pass

    elif current_collector_design == 'punched':
        # Add logic for punched design
        pass

    message = ds.html.Div([
        ds.html.Br(), ds.html.Br(),
        ds.html.P([ds.html.B("Coated Area: ", style={'font-weight': '900'}), f"{current_collector.coated_area} cm²"]),
        ds.html.P([ds.html.B("Current Collector Mass: ", style={'font-weight': '900'}), f"{current_collector.mass} g"]),
        ds.html.P([ds.html.B("Current Collector Cost: ", style={'font-weight': '900'}), f"{current_collector.cost} $"]),
        ds.html.Br(),
    ], style={'line-height': '0.5'})

    pickled_current_collector = base64.b64encode(pickle.dumps(current_collector)).decode('utf-8')
    return [message], {f'{electrode}_current_collector': pickled_current_collector}

    
@ds.callback(
    ds.Output({'tab': 'mechanicals', 'object': 'current_collector', 'object': 'graph', 'electrode': ds.MATCH}, 'figure'),
    ds.Input({'type': 'store', 'electrode': ds.MATCH, 'object': 'current_collector'}, 'data'),
    prevent_initial_call=True
)
def show_current_collector_graph(data):
    """
    Show the current collector graph based on the selected internal structure.

    :param data: The data for the current collector.
    :return: The updated current collector graph.
    """
    ctx = ds.callback_context
    triggered_id = ast.literal_eval(ctx.triggered[0]['prop_id'].split('.')[0])
    electrode = triggered_id['electrode']

    if data == [] or data == {}:
        return None

    pickled_current_collector = data[f'{electrode}_current_collector']
    current_collector = pickle.loads(base64.b64decode(pickled_current_collector))

    try:
        figure = current_collector.get_top_down_view()
    except ValueError as e:
        return None
    
    return figure


@ds.callback(
    ds.Output({'tab': 'mechanicals', 'object': 'encapsulation', 'object': 'div'}, 'children'),
    ds.Input('form_factor_dropdown', 'value'),
    prevent_initial_call=True
)
def show_encapsulation_options(form_factor):
    """
    Show the encapsulation options based on the selected form factor.

    :param form_factor: The selected form factor.
    :return: The updated encapsulation options.
    """
    if form_factor == 'cylindrical':

        return [
            ds.html.Br(), ds.html.Br(), ds.html.Br(),
            ds.html.H4("Cylindrical Shell"),
            SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 1, 0.2, 0.01, 1, 'cost', 'Cost ($)', div_width='500px').render(), ds.html.Br(), 
            SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 1000, 50, 0.1, 100, 'mass', 'Mass (g)', div_width='1400px').render(), ds.html.Br(), 
            SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 10, 3, 0.01, 1, 'internal_radius', 'Internal Radius (cm)', div_width='700px').render(), ds.html.Br(), 
            SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 1, 0.3, 0.01, 1, 'wall_thickness', 'Wall thickness (mm)', div_width='500px').render(), ds.html.Br(), 
            SliderWithTextInput({'object': 'encapsulation', 'type': 'cylindrical'}, 0, 50, 10, 0.01, 10, 'length', 'Length (cm)', div_width='500px').render(), ds.html.Br(), 
        ]
    
    else:
        return []
    

@ds.callback(
    [ds.Output({'type': 'store', 'object': 'encapsulation'}, 'data'),
     ds.Output({'tab': 'mechanicals', 'object': 'encapsulation', 'object': 'message'}, 'children')],
    [ds.Input({'object': 'encapsulation', 'type': 'cylindrical', 'property': ds.ALL, 'subtype': 'input'}, 'value'),
     ds.Input({'object': 'encapsulation', 'type': 'encapsulation', 'object': 'terminal', 'electrode': 'cathode', 'property': ds.ALL, 'subtype': 'input'}, 'value'),
     ds.Input({'object': 'encapsulation', 'type': 'encapsulation', 'object': 'terminal', 'electrode': 'anode', 'property': ds.ALL, 'subtype': 'input'}, 'value')],
     prevent_initial_call=True
)
def make_cylindrical_encapsulation(case_inputs, cathode_terminal_inputs, anode_terminal_inputs):
    """
    Create a cylindrical encapsulation object using the inputs from the sliders and text box.

    :param case_inputs: Inputs for the cylindrical case.
    :param cathode_terminal_inputs: Inputs for the cathode terminal.
    :param anode_terminal_inputs: Inputs for the anode terminal.
    """
    if len(case_inputs) == 0 or len(cathode_terminal_inputs) == 0 or len(anode_terminal_inputs) == 0:
        return {}, ["\u00A0"]

    try:
        cathode_terminal = Terminal(mass = cathode_terminal_inputs[0], specific_cost = cathode_terminal_inputs[1], thickness=cathode_terminal_inputs[2])
        anode_terminal = Terminal(mass = anode_terminal_inputs[0], specific_cost = anode_terminal_inputs[1], thickness=anode_terminal_inputs[2])
        shell = CylindricalShell(cost=case_inputs[0], mass=case_inputs[1], internal_radius=case_inputs[2], wall_thickness=case_inputs[3], length=case_inputs[4])

        case = CylindricalCase(
            shell=shell,
            positive_terminal=cathode_terminal,
            negative_terminal=anode_terminal
        )

    except ValueError as e:
        message = f"Error: {e}"
        return message, {}
    
    pickled_case = base64.b64encode(pickle.dumps(case)).decode('utf-8')

    message = ds.html.Div([
        ds.html.Br(),
        ds.html.P("\u00A0"),
        ds.html.Br(),
    ], style={'line-height': '0.5'})

    return {f'case': pickled_case}, message


@ds.callback(
    [ds.Output({'type': 'encapsulation', 'object': 'graph', 'view': 'top'}, 'figure'),
     ds.Output({'type': 'encapsulation', 'object': 'graph', 'view': 'side'}, 'figure')],
     ds.Input({'type': 'store', 'object': 'encapsulation'}, 'data'),
     ds.State('form_factor_dropdown', 'value'),
     prevent_initial_call=True
)
def get_encapsulation_plots(pickled_encapsulation, form_factor):
    """
    Get the encapsulation plots based on the selected form factor.

    :param pickled_encapsulation: The pickled encapsulation data.
    :param form_factor: The selected form factor.
    :return: The updated encapsulation plots.
    """
    if pickled_encapsulation == [] or pickled_encapsulation == {}:
        return None, None

    pickled_case = pickled_encapsulation['case']
    case = pickle.loads(base64.b64decode(pickled_case))

    if form_factor == 'cylindrical':
        figure_top = case.get_top_down_view()
        figure_side = case.get_side_view()
        return figure_top, figure_side
   
    else:
        return None, None


@ds.callback(
    [ds.Output({'type': 'store', 'electrode': ds.MATCH, 'object': 'electrode'}, 'data'),
     ds.Output({'tab': 'electrodes', 'object': 'message', 'electrode': ds.MATCH}, 'children')],
    [ds.Input({'type': 'store', 'electrode': ds.MATCH, 'object': 'formulation'}, 'data'),
     ds.Input({'type': 'store', 'electrode': ds.MATCH, 'object': 'current_collector'}, 'data'),
     ds.Input({'type': 'electrodes', 'electrode': ds.MATCH, 'object': 'electrode', 'property': 'mass_loading', 'subtype': 'input'}, 'value'),
     ds.Input({'type': 'electrodes', 'electrode': ds.MATCH, 'object': 'electrode', 'property': 'calender_density', 'subtype': 'input'}, 'value')],
     prevent_initial_call=True
)
def make_electrode(formulation, current_collector, mass_loading, calender_density):
    """
    Create an electrode object using the inputs from the sliders and text box.

    :param formulation: The formulation data.
    :param current_collector: The current collector data.
    :param mass_loading: The mass loading value.
    :param calender_density: The calender density value.
    """
    ctx = ds.callback_context
    triggered_id = ast.literal_eval(ctx.triggered[0]['prop_id'].split('.')[0])
    valence = triggered_id['electrode']

    if formulation == [] or formulation == {} or formulation == None:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" No formulation specified. Please create a {valence} formulation."])
        return {}, [message]

    if current_collector == [] or current_collector == {} or formulation == None:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" No current collector specified. Please create a {valence} current collector."])
        return {}, [message]
    
    if mass_loading is None or calender_density is None:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" Mass loading and calender density must be specified."])
        return {}, [message]

    pickled_formulation = formulation['formulation']
    formulation = pickle.loads(base64.b64decode(pickled_formulation))

    pickled_current_collector = current_collector[f'{valence}_current_collector']
    current_collector = pickle.loads(base64.b64decode(pickled_current_collector))

    if valence == 'cathode':

        try:
            electrode = Cathode(
                formulation=formulation,
                current_collector=current_collector,
                mass_loading=mass_loading,
                calender_density=calender_density
            )
        except ValueError as e:
            message = f"Error: {e}"
            return {}, [message]
        
    elif valence == 'anode':

        try:
            electrode = Anode(
                formulation=formulation,
                current_collector=current_collector,
                mass_loading=mass_loading,
                calender_density=calender_density
            )
        except ValueError as e:
            message = f"Error: {e}"
            return {}, [message]

    pickled_electrode = base64.b64encode(pickle.dumps(electrode)).decode('utf-8')

    message = ds.html.Div([
        ds.html.Br(), ds.html.Br(),
        ds.html.Br(),
    ], style={'line-height': '0.5'})

    return {f'{valence}_electrode': pickled_electrode}, [message]


@ds.callback(
    ds.Output({'type': 'div', 'object': 'electrode_assembly'}, 'children'),
    ds.Input('form_factor_dropdown', 'value'),
    prevent_initial_call=True
)
def show_electrode_assembly_inputs(form_factor):
    """
    Show the electrode assembly options based on the selected form factor.

    :param form_factor: The selected form factor.
    :return: The updated electrode assembly options.
    """
    if form_factor == 'cylindrical':
        return [
            ds.html.Br(),
            SliderWithTextInput({'type': 'cylindrical', 'object': 'electrode_assembly'}, 0, 10, 2, 0.01, 1, 'die_diameter', 'Die Diameter (mm)', div_width='800px').render(), ds.html.Br()
        ]
    else:
        return []


@ds.callback(
    [ds.Output({'type': 'store', 'object': 'electrode_assembly'}, 'data'),
     ds.Output({'tab': 'electrodes', 'object': 'message', 'type': 'electrode_assembly'}, 'children'),
     ds.Output({'tab': 'electrodes', 'object': 'graph', 'type': 'electrode_assembly'}, 'figure')],
    [ds.Input({'type': 'store', 'electrode': 'cathode', 'object': 'electrode'}, 'data'),
     ds.Input({'type': 'store', 'electrode': 'anode', 'object': 'electrode'}, 'data'),
     ds.Input({'type': 'store', 'component': 'separator'}, 'data'),
     ds.Input({'type': 'cylindrical', 'object': 'electrode_assembly', 'property': 'die_diameter', 'subtype': 'input'}, 'value')],
     ds.State('internal_structure_dropdown', 'value'),
     prevent_initial_call=True
)
def make_electrode_assembly(pickled_cathode, pickled_anode, pickled_separator, die_diameter, internal_structure):
    """
    Create an electrode assembly object using the inputs from the sliders and text box.

    :param pickled_cathode: The pickled cathode data.
    :param pickled_anode: The pickled anode data.
    :param pickled_separator: The pickled separator data.
    :param die_diameter: The die diameter value.
    """
    if pickled_cathode == [] or pickled_cathode == {}:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" No cathode formulation specified."])
        return {}, [message], None

    if pickled_anode == [] or pickled_anode == {}:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" No anode formulation specified."])
        return {}, [message], None

    if pickled_separator == [] or pickled_separator == {}:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" No separator specified."])
        return {}, [message], None

    if die_diameter is None:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" Die diameter must be specified."])
        return {}, [message], None

    pickled_cathode = pickled_cathode['cathode_electrode']
    cathode = pickle.loads(base64.b64decode(pickled_cathode))

    pickled_anode = pickled_anode['anode_electrode']
    anode = pickle.loads(base64.b64decode(pickled_anode))

    pickled_separator = pickled_separator['separator']
    separator = pickle.loads(base64.b64decode(pickled_separator))
    
    if internal_structure == 'wound':

        try:
            electrode_assembly = CylindricalJellyRoll(
                cathode=cathode,
                anode=anode,
                separator=separator,
                internal_die_diameter=die_diameter
            )
        except ValueError as e:
            message = f"Error: {e}"
            return {}, [message], None
        
        message = ds.html.Div([
            ds.html.Br(), ds.html.Br(),
            ds.html.P([ds.html.B("Cost: ", style={'font-weight': '900'}), f"{electrode_assembly.cost} $"]),
            ds.html.P([ds.html.B("Mass: ", style={'font-weight': '900'}), f"{electrode_assembly.mass} g"]),
            ds.html.P([ds.html.B("Pore Volume: ", style={'font-weight': '900'}), f"{electrode_assembly.pore_volume} cm³"]),
            ds.html.P([ds.html.B("Active Area: ", style={'font-weight': '900'}), f"{electrode_assembly.active_geometric_area} cm²"]),
            ds.html.P([ds.html.B("Radius: ", style={'font-weight': '900'}), f"{electrode_assembly.radius} cm"]),
            ds.html.P([ds.html.B("Number Of Turns: ", style={'font-weight': '900'}), f"{electrode_assembly.n_turns}"]),
            ds.html.Br(),
        ], style={'line-height': '0.5'})

    elif internal_structure == 'stacked':
        return {}, [ds.html.P("Stacked structure not implemented yet.")], None

    pickled_electrode_assembly = base64.b64encode(pickle.dumps(electrode_assembly)).decode('utf-8')

    figure = electrode_assembly.get_top_down_view(width=1400, height=1400)

    return {'electrode_assembly': pickled_electrode_assembly}, message, figure


@ds.callback(
    [ds.Output({'type': 'cell_properties_text'}, 'children'),
     ds.Output({'type': 'theoretical_curve_placeholder'}, 'children'),
     ds.Output({'type': 'cost_mass_placeholder'}, 'children'),
     ds.Output({'type': 'store', 'object': 'cell'}, 'data')],
    [ds.Input('form_factor_dropdown', 'value'),
     ds.Input({'type': 'store', 'object': 'electrode_assembly'}, 'data'),
     ds.Input({'type': 'store', 'component': 'electrolyte'}, 'data'),
     ds.Input({'type': 'mechanicals', 'property': 'electrolyte_overfill', 'subtype': 'input'}, 'value'),
     ds.Input({'type': 'store', 'object': 'encapsulation'}, 'data'),
     ds.Input({'type': 'operation', 'property': 'capacity_range', 'subtype': 'range_slider'}, 'drag_value'),
     ds.Input({'type': 'operation', 'property': 'voltage_range', 'subtype': 'range_slider'}, 'drag_value')],
     prevent_initial_call=True
)
def make_cell(form_factor, pickled_electrode_assembly, pickled_electrolyte, electrolyte_overfill, pickled_case, capacity_range, voltage_range):
    """
    Create a cell object using the inputs from the sliders and text box.

    :param form_factor: The selected form factor.
    :param pickled_electrode_assembly: The pickled electrode assembly data.
    :param pickled_electrolyte: The pickled electrolyte data.
    :param electrolyte_overfill: The electrolyte overfill value.
    :param pickled_case: The pickled case data.
    :param capacity_range: The capacity range value.
    """

    if pickled_electrode_assembly == [] or pickled_electrode_assembly == {} or pickled_electrode_assembly is None:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" No electrode assembly specified."], style={'margin-left': '20px'})
        return [message], None, None, {}

    if pickled_case == [] or pickled_case == {} or pickled_electrode_assembly is None:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" No encapsulation specified."], style={'margin-left': '20px'})
        return [message], None, None, {}

    if pickled_electrolyte == [] or pickled_electrolyte == {} or pickled_electrode_assembly is None:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" No electrolyte specified."], style={'margin-left': '20px'})
        return [message], None, None, {}

    if electrolyte_overfill is None:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" Electrolyte overfill must be specified."], style={'margin-left': '20px'})
        return [message], None, None, {}

    if capacity_range is None or len(capacity_range) == 0:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" Capacity range must be specified."], style={'margin-left': '20px'})
        return [message], None, None, {}
    
    if voltage_range is None or len(voltage_range) == 0:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f" Voltage range must be specified."], style={'margin-left': '20px'})
        return [message], None, None, {}
    
    pickled_electrode_assembly = pickled_electrode_assembly['electrode_assembly']
    electrode_assembly = pickle.loads(base64.b64decode(pickled_electrode_assembly))

    pickled_electrolyte = pickled_electrolyte['electrolyte']
    electrolyte = pickle.loads(base64.b64decode(pickled_electrolyte))

    pickled_case = pickled_case['case']
    case = pickle.loads(base64.b64decode(pickled_case))

    if form_factor == 'cylindrical':

        try:
            cell = CylindricalCell(
                electrode_assembly=electrode_assembly,
                electrolyte=electrolyte,
                encapsulation=case,
                electrolyte_overfill=electrolyte_overfill,
                reversible_capacity=capacity_range[1],
                irreversible_capacity=capacity_range[0]
            )
        except ValueError as e:
            message = f"Error: {e}"
            return [message], None, None, {}
        
    else:
        return None, None, None, {}
        
    theoretical_curve = cell.get_capacity_voltage_plot(background_color='#e3e5e6', upper_v_limit=voltage_range[1], lower_v_limit=voltage_range[0], width=960, height=550)
    theoretical_curve_div = ds.dcc.Graph(id='theoretical_curve_fig', figure=theoretical_curve, style={'margin-left': '20px'})    

    breakdown_div = ds.html.Div([
        ds.dcc.Graph(id='cost_breakdown_fig', figure=cell.get_cost_breakdown_plot(background_color='#e3e5e6', width=550, height=550)),
        ds.dcc.Graph(id='mass_breakdown_fig', figure=cell.get_mass_breakdown_plot(background_color='#e3e5e6', width=550, height=550), style={'margin-left': '-50px'})
    ], style={'display': 'flex', 'flex-direction': 'row', 'align-items': 'center'})

    message = ds.html.Div([
        ds.html.Br(), ds.html.Br(),
        ds.html.P([ds.html.B("Cost: ", style={'font-weight': '900'}), f"{cell.cost} $"]),
        ds.html.P([ds.html.B("Normalized Cost: ", style={'font-weight': '900'}), f"{cell.normalized_cost} $/kWh"]),
        ds.html.P([ds.html.B("Mass: ", style={'font-weight': '900'}), f"{cell.mass} g"]),
        ds.html.P([ds.html.B("Volume: ", style={'font-weight': '900'}), f"{cell.volume} cm³"]),
        ds.html.P([ds.html.B("Energy: ", style={'font-weight': '900'}), f"{cell.energy} Wh"]),
        ds.html.P([ds.html.B("Energy Density: ", style={'font-weight': '900'}), f"{cell.energy_density} Wh/kg"]),
        ds.html.P([ds.html.B("Specific Energy: ", style={'font-weight': '900'}), f"{cell.specific_energy} Wh/L"]),
        ds.html.Br(),
    ], style={'line-height': '0.5'})    
    
    return [message], [theoretical_curve_div], [breakdown_div], {}
    
