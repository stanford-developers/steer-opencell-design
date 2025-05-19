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
from SteerEnergyStorage.Materials.CurrentCollectors import CurrentCollector, NotchedCurrentCollector, TabWeldedCurrentCollector, TablessCurrentCollector, PunchedCurrentCollector
from SteerEnergyStorage.Materials.Electrolytes import Electrolyte
from SteerEnergyStorage.Materials.other import Terminal, Laminate, Tape
from SteerEnergyStorage.Constructions.Containers import CylindricalCase, CylindricalCanister, CylindricalLidAssembly, CylindricalTerminalCollector
from SteerEnergyStorage.Constructions.Containers import Pouch, PrismaticCase, PrismaticLid, PrismaticShell
from SteerEnergyStorage.Constructions.Containers import PrismaticCase, PrismaticLid, PrismaticShell
from SteerEnergyStorage.Constructions.Electrodes import Cathode, Anode
from SteerEnergyStorage.Formulations.ElectrodeAssemblies import CylindricalJellyRoll, Stack
from SteerEnergyStorage.Constructions.Cells import CylindricalCell, CylindricalCase, StackedPouchCell, StackedPrismaticCell


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
        return ds.no_update

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
     Prevent_initial_call=True
)
def sync_slider_and_input_material_selectors_with_electrode(slider_value, input_value):
    """
    Synchronize the slider and input box values.

    :param slider_value: The value from the slider.
    :param input_value: The value from the input box.
    :return: The synchronized values for both components.
    """
    ctx = ds.callback_context

    if not ctx.triggered:
        return ds.no_update, ds.no_update

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
    prevent_initial_call=True
)
def update_formulation(data_list):
    """
    Update the formulation properties text and store the formulation data.

    :param data_list: List of data from the stores.
    :return: The updated formulation properties text and store data.
    """
    if data_list == [] or data_list == [{}]:
        return ds.no_update, ds.no_update
    
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
         prevent_initial_call=True
)
def sync_generic_sliders(slider_val, input_val):
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
        return ds.no_update, ds.no_update
    

@ds.callback(
        [ds.Output({'type': ds.MATCH, 'object': ds.MATCH,'subtype': 'slider', 'property': ds.MATCH}, 'value'),
         ds.Output({'type': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': ds.MATCH}, 'value')],
        [ds.Input({'type': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': ds.MATCH}, 'drag_value'),
         ds.Input({'type': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': ds.MATCH}, 'value')],
         prevent_initial_call=True
)
def sync_generic_sliders_2(slider_val, input_val):
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
        return ds.no_update, ds.no_update


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
    [ds.Input({'type': 'mechanicals', 'subtype': 'input', 'property': ds.ALL}, 'value')],
     prevent_initial_call=True
)
def make_separator(inputs):
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
        separator = Separator(
            thickness=inputs[0],
            areal_cost=inputs[1], 
            density=inputs[2],  
            width=inputs[3],
            porosity=inputs[4], 
            fold_length=inputs[5], 
        )
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
        options = [
            {'label': 'Tabless', 'value': 'tabless'}, 
            {'label': 'Notched', 'value': 'notched'}, 
            # {'label': 'Tab Welded', 'value': 'tab_welded'}
            ]
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
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 6000, 1000, 0.1, 100, 'length', 'Length (mm)', div_width='1400px').render(), ds.html.Br(), 
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 400, 120, 0.1, 20, 'width', 'Width  (mm)', div_width='600px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 100, 15, 0.1, 5, 'thickness', 'Thickness  (μm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 50, 3, 0.1, 10, 'tab_width', 'Tab Width (mm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 200, 30, 0.1, 10, 'tab_length', 'Tab Length (mm)', div_width='600px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 200, 30, 0.1, 10, 'tab_spacing', 'Tab Spacing (mm)', div_width='600px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'notched', 'object': 'current_collector', 'electrode': electrode}, 0, 500, 0, 0.1, 50, 'bare_length', 'Bare Tape (mm)', div_width='600px').render(), ds.html.Br(),
        ]
    
    elif design == 'tabless':
        return [
            ds.html.Br(), 
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 6000, 1000, 0.1, 100, 'length', 'Length (mm)', div_width='1400px').render(), ds.html.Br(), 
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 400, 120, 0.1, 20, 'width', 'Width  (mm)', div_width='600px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 100, 15, 0.1, 5, 'thickness', 'Thickness  (μm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 50, 3, 0.1, 10, 'tab_width', 'Tab Width (mm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'tabless', 'object': 'current_collector', 'electrode': electrode}, 0, 500, 0, 0.1, 50, 'bare_length', 'Bare Tape (mm)', div_width='600px').render(), ds.html.Br(),
        ]

    elif design == 'tab_welded':
        return [
            ds.html.P("Tab welded current collector selected for " + electrode),
            ds.html.Br(),
            ds.html.P("Additional parameters for tab welded current collector can be added here.")
        ]
    
    elif design == 'punched':
        def_tab_pos = 30 if electrode == 'cathode' else 80
        return [
            ds.html.Br(), 
            SliderWithTextInput({'type': 'punched', 'object': 'current_collector', 'electrode': electrode}, 0, 500, 110, 0.1, 50, 'length', 'Length (mm)', div_width='1100px').render(), ds.html.Br(), 
            SliderWithTextInput({'type': 'punched', 'object': 'current_collector', 'electrode': electrode}, 0, 500, 110, 0.1, 50, 'width', 'Width (mm)', div_width='1100px').render(), ds.html.Br(), 
            SliderWithTextInput({'type': 'punched', 'object': 'current_collector', 'electrode': electrode}, 0, 200, 40, 0.1, 40, 'tab_width', 'Tab Width (mm)', div_width='400px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'punched', 'object': 'current_collector', 'electrode': electrode}, 0, 200, 20, 0.1, 40, 'tab_height', 'Tab Height (mm)', div_width='400px').render(), ds.html.Br(), 
            SliderWithTextInput({'type': 'punched', 'object': 'current_collector', 'electrode': electrode}, 0, 500, def_tab_pos, 0.1, 50, 'tab_position', 'Tab Position (mm)', div_width='1100px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'punched', 'object': 'current_collector', 'electrode': electrode}, 0, 100, 15, 0.1, 5, 'thickness', 'Thickness  (μm)', div_width='400px').render(), ds.html.Br(),  
        ]


@ds.callback(
    [ds.Output({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': 'density'}, 'value'),
     ds.Output({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': 'density'}, 'value'),
     ds.Output({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': 'specific_cost'}, 'value'),
     ds.Output({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': 'specific_cost'}, 'value')],
    [ds.Input({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'text_input', 'property': 'name'}, 'value'),
     ds.Input({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': 'density'}, 'drag_value'),
     ds.Input({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': 'density'}, 'value'),
     ds.Input({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': 'specific_cost'}, 'drag_value'),
     ds.Input({'electrode': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': 'specific_cost'}, 'value')],
     prevent_initial_call=True
)
def update_material_selector_properties_and_sync(material_formula, density_slider_value, density_input_value, specific_cost_slider_value, specific_cost_input_value):
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
    [ds.Output({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': 'density'}, 'value'),
     ds.Output({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': 'density'}, 'value'),
     ds.Output({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': 'specific_cost'}, 'value'),
     ds.Output({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': 'specific_cost'}, 'value')],
    [ds.Input({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'text_input', 'property': 'name'}, 'value'),
     ds.Input({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': 'density'}, 'drag_value'),
     ds.Input({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': 'density'}, 'value'),
     ds.Input({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'slider', 'property': 'specific_cost'}, 'drag_value'),
     ds.Input({'component': ds.MATCH, 'object': ds.MATCH, 'subtype': 'input', 'property': 'specific_cost'}, 'value')],
     prevent_initial_call=True
)
def update_encapsulation_material_selector_properties_and_sync(material_formula, density_slider_value, density_input_value, specific_cost_slider_value, specific_cost_input_value):
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
        terminal = CylindricalTerminalCollector(formula=material_formula, diameter=1, thickness=1)
        return terminal.density, terminal.density, terminal.specific_cost, terminal.specific_cost
    
    elif triggered_id and triggered_id['subtype'] == 'slider':
        return density_slider_value, density_slider_value, specific_cost_slider_value, specific_cost_slider_value
    
    elif triggered_id and triggered_id['subtype'] == 'input':
        return density_input_value, density_input_value, specific_cost_input_value, specific_cost_input_value

    return 4, 4, 15, 15


@ds.callback(
        [ds.Output({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'slider'}, 'value'),
         ds.Output({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'input'}, 'value')],
        [ds.Input({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'slider'}, 'drag_value'),
         ds.Input({'type': ds.MATCH, 'object': ds.MATCH, 'electrode': ds.MATCH, 'property': ds.MATCH, 'subtype': 'input'}, 'value')],
         prevent_initial_call=True
)
def sync_generic_sliders_with_electrode(slider_val, input_val):
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
        return ds.no_update, ds.no_update
    

@ds.callback(
        [ds.Output({'tab': 'mechanicals', 'object': 'current_collector', 'object': 'message', 'electrode': ds.MATCH}, 'children'),
         ds.Output({'type': 'store', 'electrode': ds.MATCH, 'object': 'current_collector'}, 'data')],
        [ds.Input({'type': ds.ALL, 'object': 'current_collector', 'electrode': ds.MATCH, 'subtype': 'slider', 'property': ds.ALL}, 'drag_value'),
         ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'text_input', 'property': 'name'}, 'value'),
         ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'slider', 'property': 'density'}, 'drag_value'),
         ds.Input({'electrode': ds.MATCH, 'object': 'current_collector', 'subtype': 'slider', 'property': 'specific_cost'}, 'drag_value'),
         ds.Input({'type': 'mechanicals', 'object': 'current_collector', 'electrode': ds.MATCH, 'feature': 'design'}, 'value')],
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
            current_collector = TablessCurrentCollector(
                formula=material_formula,
                length=properties[0],
                width=properties[1],
                thickness=properties[2],
                tab_width=properties[3],
                density=material_density,
                specific_cost=material_specific_cost,
                bare_length=properties[4]
            )

        except ValueError as e:
            message = f"Error: {e}"
            return message, {}

    elif current_collector_design == 'tab_welded':
        # Add logic for tab welded design
        pass

    elif current_collector_design == 'punched':
        
        try:
            current_collector = PunchedCurrentCollector(
                formula=material_formula,
                length=properties[0],
                width=properties[1],
                tab_width=properties[2],
                tab_height=properties[3],
                tab_position=properties[4],
                thickness=properties[5],
                density=material_density,
                specific_cost=material_specific_cost
            )
        except ValueError as e:
            message = f"Error: {e}"
            return message, {}

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
    [ds.Input({'type': 'store', 'electrode': ds.MATCH, 'object': 'current_collector'}, 'data'),
     ds.Input({'type': 'mechanicals', 'object': 'current_collector', 'electrode': ds.MATCH, 'feature': 'design'}, 'value')],
    prevent_initial_call=True
)
def show_current_collector_graph(data, design):
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

    if design == 'notched' or design == 'tabless':
        figure = current_collector.get_top_down_view(width=1200, height=700)
    elif design == 'punched':
        figure = current_collector.get_top_down_view(width=700, height=700)

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
        return [cylindrical_encapsulation]
    
    elif form_factor == 'pouch':
        return [pouch_encapsulation]
    
    elif form_factor == 'prismatic':
        return [prismatic_encapsulation]
    
    else:
        return []


@ds.callback(
    [ds.Output({'type': 'store', 'object': 'encapsulation'}, 'data'),
     ds.Output({'tab': 'mechanicals', 'object': 'encapsulation', 'object': 'message'}, 'children'),
     ds.Output({'tab': 'mechanicals', 'object': 'encapsulation', 'object': 'plot'}, 'children')],
    [ds.Input({'object': 'encapsulation', 'type': ds.ALL, 'property': ds.ALL, 'subtype': 'input'}, 'value'),
     ds.Input({'object': 'encapsulation', 'component': ds.ALL, 'subtype': 'input', 'property': 'specific_cost'}, 'value'),
     ds.Input({'object': 'encapsulation', 'component': ds.ALL, 'subtype': 'input', 'property': 'density'}, 'value'),
     ds.Input({'object': 'encapsulation', 'component': ds.ALL, 'subtype': 'text_input', 'property': 'name'}, 'value'),
     ds.Input('form_factor_dropdown', 'value')],
    prevent_initial_call=True
)
def make_encapsulation(inputs, specific_costs, densities, formulas, form_factor):
    """
    Create a cylindrical encapsulation object using the inputs from the sliders and text box.

    :param case_inputs: Inputs for the cylindrical case.
    :param cathode_terminal_inputs: Inputs for the cathode terminal.
    :param anode_terminal_inputs: Inputs for the anode terminal.
    """
    print(f"inputs: {inputs}")
    print(f"specific_costs: {specific_costs}")
    print(f"densities: {densities}")
    print(f"formulas: {formulas}")

    if len(inputs) == 0:
        return {}, ["\u00A0"]

    if form_factor == 'cylindrical':

        try:
            can = CylindricalCanister(formulas[0], outer_diameter=inputs[0], wall_thickness=inputs[1], length=inputs[2], density=densities[0], specific_cost=specific_costs[0])
            lid = CylindricalLidAssembly(cost=inputs[3], mass=inputs[4], thickness=inputs[5])
            anode_cc = CylindricalTerminalCollector(formula=formulas[1], diameter=inputs[6], thickness=inputs[7], fill_factor=inputs[8])
            cathode_cc = CylindricalTerminalCollector(formula=formulas[2], diameter=inputs[9], thickness=inputs[10], fill_factor=inputs[11])
            case = CylindricalCase(canister=can, lid_assembly=lid, anode_terminal_collector=anode_cc, cathode_terminal_collector=cathode_cc)

        except ValueError as e:
            message = f"Error: {e}"
            return {}, [message], []
        
        top_down = case.get_top_down_view()
        bottom_up = case.get_bottom_up_view()
        side = case.get_side_view()

        figure = ds.html.Div([
                    ds.html.Div([
                        ds.html.Div(ds.dcc.Graph(id='cylindrical_top_down', figure=top_down, style={'width': '100%', 'height': '400px'}), style={'margin-bottom': '20px'}),
                        ds.html.Div(ds.dcc.Graph(id='cylindrical_bottom_up', figure=bottom_up, style={'width': '100%', 'height': '400px'})),
                    ], style={'width': '40%', 'display': 'inline-block', 'vertical-align': 'top'}),
                    ds.html.Div(ds.dcc.Graph(id='cylindrical_side', figure=side, style={'width': '100%', 'height': '820px'}),style={'width': '58%', 'display': 'inline-block', 'margin-left': '2%'})
                ])
    
    elif form_factor == 'pouch':

        try:
            cathode_terminal = Terminal(mass = cathode_terminal_inputs[0], specific_cost = cathode_terminal_inputs[1], thickness=cathode_terminal_inputs[2])
            anode_terminal = Terminal(mass = anode_terminal_inputs[0], specific_cost = anode_terminal_inputs[1], thickness=anode_terminal_inputs[2])
            laminate = Laminate(thickness=inputs[0], areal_mass=inputs[1], areal_cost=inputs[2])
            tape = Tape(mass=inputs[3])

            case = Pouch(
                laminate=laminate,
                tape=tape,
                heat_seal_size_sides=inputs[4],
                heat_seal_size_top=inputs[5],
                positive_terminal=cathode_terminal,
                negative_terminal=anode_terminal
            )

        except ValueError as e:
            message = f"Error: {e}"
            return {}, [message], []
        
    elif form_factor == 'prismatic':
        
        try:
            lid = PrismaticLid(mass=inputs[0], cost=inputs[1], external_width=inputs[2], internal_width=inputs[3])
            shell = PrismaticShell(mass=inputs[4], cost=inputs[5], internal_length=inputs[6], internal_width=inputs[7], internal_height=inputs[8], wall_thickness=inputs[9])
            case = PrismaticCase(lid=lid, shell=shell)

        except ValueError as e:
            message = f"Error: {e}"
            return {}, [message], []

    pickled_case = base64.b64encode(pickle.dumps(case)).decode('utf-8')

    message = ds.html.Div([
        ds.html.Br(),
        ds.html.P("\u00A0"),
        ds.html.Br(),
    ], style={'line-height': '0.5'})

    return {f'case': pickled_case}, message, figure


@ds.callback(
    [ds.Output({'type': 'encapsulation', 'object': 'graph', 'view': 'top'}, 'figure'),
     ds.Output({'type': 'encapsulation', 'object': 'graph', 'view': 'side'}, 'figure'),
     ds.Output({'type': 'encapsulation', 'object': 'graph', 'view': 'top'}, 'style'),
     ds.Output({'type': 'encapsulation', 'object': 'graph', 'view': 'side'}, 'style')],
     [ds.Input({'type': 'store', 'object': 'encapsulation'}, 'data'),
      ds.Input('form_factor_dropdown', 'value')],
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
        return None, None, {'display': 'none'}, {'display': 'none'}

    pickled_case = pickled_encapsulation['case']
    case = pickle.loads(base64.b64decode(pickled_case))

    if form_factor == 'cylindrical':
        figure_top = case.get_top_down_view()
        figure_side = case.get_side_view()
        return figure_top, figure_side, ds.no_update, ds.no_update
   
    else:
        return None, None, {'display': 'none'}, {'display': 'none'}


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
    ds.Input('internal_structure_dropdown', 'value'),
    prevent_initial_call=True
)
def show_electrode_assembly_inputs(internal_construction):
    """
    Show the electrode assembly options based on the selected form factor.

    :param form_factor: The selected form factor.
    :return: The updated electrode assembly options.
    """
    if internal_construction == 'wound':
        return [
            ds.html.Br(),
            SliderWithTextInput({'type': 'electrode_assembly'}, 0, 10, 2, 0.01, 1, 'die_diameter', 'Die diameter (mm)', div_width='800px').render(), ds.html.Br()
        ]
    elif internal_construction == 'stacked':
        return [
            ds.html.Br(),
            SliderWithTextInput({'type': 'electrode_assembly'}, 0, 100, 10, 1, 10, 'n_stacks', 'Number of electrode stacks', div_width='1000px').render(), ds.html.Br(),
            SliderWithTextInput({'type': 'electrode_assembly'}, 0, 6, 1, 1, 1, 'separator_wraps', 'Additional separator wraps', div_width='700px').render(), ds.html.Br()
        ]


@ds.callback(
    [ds.Output({'type': 'store', 'object': 'electrode_assembly'}, 'data'),
     ds.Output({'tab': 'electrodes', 'object': 'message', 'type': 'electrode_assembly'}, 'children'),
     ds.Output({'tab': 'electrodes', 'object': 'graph', 'type': 'electrode_assembly'}, 'children')],
    [ds.Input({'type': 'store', 'electrode': 'cathode', 'object': 'electrode'}, 'data'),
     ds.Input({'type': 'store', 'electrode': 'anode', 'object': 'electrode'}, 'data'),
     ds.Input({'type': 'store', 'component': 'separator'}, 'data'),
     ds.Input({'type': 'electrode_assembly', 'property': ds.ALL, 'subtype': 'input'}, 'value'),
     ds.Input({'type': 'store', 'object': 'encapsulation'}, 'data'),
     ds.Input('internal_structure_dropdown', 'value')],
     prevent_initial_call=True
)
def make_electrode_assembly(pickled_cathode, pickled_anode, pickled_separator, assembly_parameters, encapsulation, internal_structure):
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

    if assembly_parameters is None or len(assembly_parameters) == 0:
        message = ds.html.P([ds.html.B("Warning: ", style={'font-weight': '900'}), f"Assembly inputs are required."])
        return {}, [message], None
    
    if encapsulation == [] or encapsulation == {} or encapsulation == None:
        encapsulation = None
    else:
        pickled_case = encapsulation['case']
        case = pickle.loads(base64.b64decode(pickled_case))

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
                internal_die_diameter=assembly_parameters[0],
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
            ds.html.P([ds.html.B("Radius: ", style={'font-weight': '900'}), f"{electrode_assembly.radius} mm"]),
            ds.html.P([ds.html.B("Number Of Turns: ", style={'font-weight': '900'}), f"{electrode_assembly.n_turns}"]),
            ds.html.Br(),
        ], style={'line-height': '0.5'}) 

        figure_top = electrode_assembly.get_top_down_view(encapsulation=case, width=700, height=900)
        figure_side = electrode_assembly.get_side_view(encapsulation=case, width=600, height=900)

        figure_div = ds.html.Div([
            ds.html.Div(ds.dcc.Graph(id='graph-1', figure=figure_top), style={'width': '48%', 'display': 'inline-block', 'vertical-align': 'top'}),
            ds.html.Div(ds.dcc.Graph(id='graph-2', figure=figure_side), style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%', 'vertical-align': 'top'})
            ])

    elif internal_structure == 'stacked':
        
        try:
            electrode_assembly = Stack(
                cathode=cathode,
                anode=anode,
                separator=separator,
                n_layers=assembly_parameters[0],
                additional_separator_wraps=assembly_parameters[1]
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
            ds.html.Br(),
        ], style={'line-height': '0.5'})

        figure = None

    else: 
        return {}, ["\u00A0"], None

    pickled_electrode_assembly = base64.b64encode(pickle.dumps(electrode_assembly)).decode('utf-8')

    return {'electrode_assembly': pickled_electrode_assembly}, message, figure_div


@ds.callback(
        
    [ds.Output({'type': 'cell_properties_text'}, 'children'),
     ds.Output({'type': 'theoretical_curve_placeholder'}, 'children'),
     ds.Output({'type': 'cost_mass_placeholder'}, 'children'),
     ds.Output({'type': 'store', 'object': 'cell'}, 'data')],
 
    [ds.Input({'type': 'store', 'object': 'electrode_assembly'}, 'data'),
     ds.Input({'type': 'store', 'component': 'electrolyte'}, 'data'),
     ds.Input({'type': 'mechanicals', 'property': 'electrolyte_overfill', 'subtype': 'input'}, 'value'),
     ds.Input({'type': 'store', 'object': 'encapsulation'}, 'data'),
     ds.Input({'type': 'operation', 'property': 'capacity_range', 'subtype': 'range_slider'}, 'drag_value'),
     ds.Input({'type': 'operation', 'property': 'voltage_range', 'subtype': 'range_slider'}, 'drag_value'),
     ds.Input('form_factor_dropdown', 'value'),
     ds.Input('internal_structure_dropdown', 'value'),
     ds.Input('num_electrode_assemblies', 'value')],

     ds.State({'type': 'store', 'object': 'cell'}, 'data'),

     prevent_initial_call=True
)
def make_cell(pickled_electrode_assembly: dict, 
              pickled_electrolyte: dict, 
              electrolyte_overfill: float, 
              pickled_case: dict, 
              capacity_range: list, 
              voltage_range: list, 
              form_factor: str, 
              internal_structure: str, 
              num_electrode_assemblies: int, 
              pickled_cell: dict):
    """
    Create a cell object using the inputs from the sliders and text box.

    :param form_factor: The selected form factor.
    :param pickled_electrode_assembly: The pickled electrode assembly data.
    :param pickled_electrolyte: The pickled electrolyte data.
    :param electrolyte_overfill: The electrolyte overfill value.
    :param pickled_case: The pickled case data.
    :param capacity_range: The capacity range value.
    """
    ctx = ds.callback_context
    triggered_id = ctx.triggered_prop_ids

    if triggered_id == {'property': 'voltage_range', 'subtype': 'range_slider', 'type': 'operation'}:
        cell = pickle.loads(base64.b64decode(pickled_cell['cell']))
        theoretical_curve = cell.get_capacity_voltage_plot(background_color='#e3e5e6', upper_v_limit=voltage_range[1], lower_v_limit=voltage_range[0], width=960, height=550)
        theoretical_curve_div = ds.dcc.Graph(id='theoretical_curve_fig', figure=theoretical_curve, style={'margin-left': '20px'})
        return ds.no_update, theoretical_curve_div, ds.no_update, ds.no_update

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
        
    elif form_factor == 'pouch' and internal_structure == 'stacked':
    
        try:
            cell = StackedPouchCell(
                stack=electrode_assembly,
                pouch=case,
                electrolyte=electrolyte,
                electrolyte_overfill=electrolyte_overfill,
                reversible_capacity=capacity_range[1],
                irreversible_capacity=capacity_range[0],
                n_stacks=num_electrode_assemblies
            )
        except ValueError as e:
            message = f"Error: {e}"
            return [message], None, None, {}
        
    elif form_factor == 'prismatic' and internal_structure == 'stacked':

        try:
            cell = StackedPrismaticCell(
                stack=electrode_assembly,
                prismatic_case=case,
                electrolyte=electrolyte,
                electrolyte_overfill=electrolyte_overfill,
                reversible_capacity=capacity_range[1],
                irreversible_capacity=capacity_range[0],
                n_stacks=num_electrode_assemblies
            )
        except ValueError as e:
            message = f"Error: {e}"
            return [message], None, None, {}
            
    else:
        return None, None, None, {}
        
    theoretical_curve = cell.get_capacity_voltage_plot(background_color='#e3e5e6', upper_v_limit=voltage_range[1], lower_v_limit=voltage_range[0], width=920, height=550)
    theoretical_curve_div = ds.dcc.Graph(id='theoretical_curve_fig', figure=theoretical_curve, style={'margin-left': '20px'})    

    breakdown_div = ds.html.Div([
        ds.dcc.Graph(id='cost_breakdown_fig', figure=cell.get_cost_breakdown_plot(background_color='#e3e5e6', width=550, height=550)),
        ds.dcc.Graph(id='mass_breakdown_fig', figure=cell.get_mass_breakdown_plot(background_color='#e3e5e6', width=550, height=550), style={'margin-left': '-80px'})
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
    ], style={'line-height': '0.5'})    

    pickled_cell = base64.b64encode(pickle.dumps(cell)).decode('utf-8')
    
    return [message], [theoretical_curve_div], [breakdown_div], {'cell': pickled_cell}
    
