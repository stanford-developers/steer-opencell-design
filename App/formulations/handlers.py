from typing import List, Dict, Any, Tuple
from dash import no_update
from itertools import chain

from App.formulations.configs import FormulationConfig
from App.general.handlers import _build_basic_response, handle_cell_store_update
from App.materials.configs import MaterialType, MATERIAL_CONFIGS, MaterialConfig
from App.general.callback_helpers import generate_parameters, create_no_update_response
from App.general.cell_operations import set_object_to_cell, set_cell_to_cache
from App.database_service import BINDER_MATERIALS, CONDUCTIVE_ADDITIVE_MATERIALS

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from steer_materials.CellMaterials.Electrode import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive

from steer_core.Apps.Utils.SliderControls import create_slider_config
from steer_core.Apps.Components.MaterialSelectors import MaterialSelector, ActiveMaterialSelector


def get_material_config(formulation_config: FormulationConfig, material_tag: str) -> MaterialConfig:

    """Get the appropriate material config based on formulation and category"""

    if material_tag == 'active_material' and formulation_config.formulation_type == CathodeFormulation:
        material_type = MaterialType.CATHODE_ACTIVE_MATERIAL
    elif material_tag == 'active_material' and formulation_config.formulation_type == AnodeFormulation:
        material_type = MaterialType.ANODE_ACTIVE_MATERIAL
    elif material_tag == 'binder':
        material_type = MaterialType.BINDER
    elif material_tag == 'conductive_additive':
        material_type = MaterialType.CONDUCTIVE_ADDITIVE

    return MATERIAL_CONFIGS[material_type]


def create_material_response(material_name: str, material_config: MaterialConfig) -> List[Any]:
    """Create response for a specific material"""
    material = material_config.material_type.from_database(material_name)
    parameter_list, min_values, max_values = generate_parameters(material, material_config)
    slider_configs = create_slider_config(min_values, max_values, parameter_list)
    return _build_basic_response(slider_configs)[1:]


def process_material_category(
        dropdown_values: List[str], 
        category_name: str, 
        trigger_index: int, 
        triggered_category: str, 
        formulation_config: FormulationConfig, 
        existing_warnings: List[str]
) -> Dict[int, List[Any]]:
    
    """Process a single material category and return response dictionary"""

    material_config = get_material_config(formulation_config, category_name)
    
    response_dict = {}
    
    for i, dropdown_value in enumerate(dropdown_values):
        if triggered_category == category_name and i == trigger_index:
            response_dict[i] = create_material_response(dropdown_value, material_config)
        else:
            response_dict[i] = list(create_no_update_response(material_config, existing_warnings))[2:]
    
    return response_dict


def update_formulation_materials(
        
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    triggered_category: str,
    active_dropdown_values: List[str],
    active_weight_fractions: List[float],
    binder_dropdown_values: List[str],
    binder_weight_fractions: List[float],
    conductive_dropdown_values: List[str],
    conductive_weight_fractions: List[float]

) -> CathodeFormulation | AnodeFormulation:
    
    """Update formulation materials based on triggered category"""
    
    # Material category mappings with their data
    material_updates = {
        'active_material': {
            'dropdown_values': active_dropdown_values,
            'weight_fractions': active_weight_fractions,
            'material_classes': {
                CathodeFormulation: CathodeMaterial,
                AnodeFormulation: AnodeMaterial
            },
            'attribute': 'active_materials'
        },
        'binder': {
            'dropdown_values': binder_dropdown_values,
            'weight_fractions': binder_weight_fractions,
            'material_class': Binder,
            'attribute': 'binders'
        },
        'conductive_additive': {
            'dropdown_values': conductive_dropdown_values,
            'weight_fractions': conductive_weight_fractions,
            'material_class': ConductiveAdditive,
            'attribute': 'conductive_additives'
        }
    }
    
    if triggered_category not in material_updates:
        return
    
    update_config = material_updates[triggered_category]
    dropdown_values = update_config['dropdown_values']
    weight_fractions = update_config['weight_fractions']
    
    # Create new material dictionary
    new_material_dict = {}
    
    for weight_frac, material_name in zip(weight_fractions, dropdown_values):
        if material_name:  # Only process non-empty material names
            if triggered_category == 'active_material':
                # For active materials, determine class based on formulation type
                material_class = update_config['material_classes'][formulation_config.formulation_type]
            else:
                # For other materials, use the direct class
                material_class = update_config['material_class']
            
            material = material_class.from_database(material_name)
            new_material_dict[material] = weight_frac
    
    # Update the formulation attribute
    setattr(formulation, update_config['attribute'], new_material_dict)

    return formulation


def flatten_response_dict(response_dict: Dict[int, List[Any]]) -> Tuple[Any, ...]:
    """Flatten response dictionary into tuple format for Dash"""
    if not response_dict:
        return ()
    
    first_response = next(iter(response_dict.values()))
    num_elements = len(first_response)
    
    return tuple(
        [element for material_idx in sorted(response_dict.keys()) 
         for element in response_dict[material_idx][element_idx]]
        for element_idx in range(num_elements)
    ) 


def handle_indexed_dropdown_update(
        existing_warnings,
        trigger_id,
        cell,
        formulation,
        formulation_config,
        active_dropdown_values,
        active_weight_fractions,
        active_slider_values,
        active_input_values,
        binder_dropdown_values,
        binder_weight_fractions,
        binder_slider_values,
        binder_input_values,
        conductive_dropdown_values,
        conductive_weight_fractions,
        conductive_slider_values,
        conductive_input_values
):
    """Handle material dropdown updates with simplified functional approach"""
    trigger_index = trigger_id.get('index')
    triggered_category = trigger_id.get('material')
    
    # Process each material category
    categories = [
        ('active_material', active_dropdown_values),
        ('binder', binder_dropdown_values),
        ('conductive_additive', conductive_dropdown_values)
    ]
    
    responses = []
    for category_name, dropdown_values in categories:

        response_dict = process_material_category(
            dropdown_values, 
            category_name, 
            trigger_index, 
            triggered_category, 
            formulation_config, 
            existing_warnings
        )

        flattened_response = flatten_response_dict(response_dict)
        responses.extend(flattened_response)
    
    # Update formulation materials using helper function
    new_formulation = update_formulation_materials(
        formulation,
        formulation_config,
        triggered_category,
        active_dropdown_values,
        active_weight_fractions,
        binder_dropdown_values,
        binder_weight_fractions,
        conductive_dropdown_values,
        conductive_weight_fractions
    )

    print(f"DEBUG: new formulation active materials: {new_formulation.active_materials}")
    print(f"DEBUG: new formulation voltage cutoff: {new_formulation.voltage_cutoff}")

    # set new formulation to cell
    new_cell = set_object_to_cell(cell, new_formulation, formulation_config)

    # get the new key
    new_key = set_cell_to_cache(new_cell)

    return (existing_warnings, {'cache_key': new_key}) + tuple(responses)


def handle_cell_store_update_materials(
        
        existing_warnings: List[float], 
        formulation: CathodeFormulation | AnodeFormulation, 
        formulation_config: FormulationConfig,
        active_div_styles: List[Dict[str, Any]],
        binder_div_styles: List[Dict[str, Any]],
        conductive_div_styles: List[Dict[str, Any]],
        cathode_active_options: List[str],
        anode_active_options: List[str],

) -> Tuple[Any, Any, List[Any], List[Any], List[Any]]:
    
    """Create MaterialSelector components based on formulation structure"""

    n_active_divs = len(active_div_styles)
    n_binder_divs = len(binder_div_styles)
    n_conductive_divs = len(conductive_div_styles)

    n_active_materials = len(formulation.active_materials)
    n_binder_materials = len(formulation.binders)
    n_conductive_materials = len(formulation.conductive_additives)

    ### create style response
    # make the correct number of active divs visible
    for i in range(0, n_active_materials):
        active_div_styles[i]['display'] = 'block'

    # make the correct number of binder divs visible
    for i in range(0, n_binder_materials):
        binder_div_styles[i]['display'] = 'block'

    # make the correct number of conductive divs visible
    for i in range(0, n_conductive_materials):
        conductive_div_styles[i]['display'] = 'block'

    div_style_response = (active_div_styles + binder_div_styles + conductive_div_styles)



    ## create dropdown options response
    active_dropdown_options = []
    active_options = cathode_active_options if formulation_config.formulation_type == CathodeFormulation else anode_active_options
    for i in range(0, n_active_divs):
        if i in range(0, n_active_materials):
            active_dropdown_options.append(active_options)
        else:
            active_dropdown_options.append(no_update)

    binder_dropdown_options = []
    binder_options = BINDER_MATERIALS
    for i in range(0, n_binder_divs):
        if i in range(0, n_binder_materials):
            binder_dropdown_options.append(binder_options)
        else:
            binder_dropdown_options.append(no_update)

    conductive_dropdown_options = []
    conductive_options = CONDUCTIVE_ADDITIVE_MATERIALS
    for i in range(0, n_conductive_divs):
        if i in range(0, n_conductive_materials):
            conductive_dropdown_options.append(conductive_options)
        else:
            conductive_dropdown_options.append(no_update)

    dropdown_options_response = (active_dropdown_options + binder_dropdown_options + conductive_dropdown_options)


    ## create dropdown value response 
    active_dropdown_values = []
    for i in range(0, n_active_divs):
        if i in range(0, n_active_materials):
            material_name = list(formulation.active_materials.keys())[i].name
            active_dropdown_values.append(material_name)
        else:
            active_dropdown_values.append(None)

    binder_dropdown_values = []
    for i in range(0, n_binder_divs):
        if i in range(0, n_binder_materials):
            material_name = list(formulation.binders.keys())[i].name
            binder_dropdown_values.append(material_name)
        else:
            binder_dropdown_values.append(None)

    conductive_dropdown_values = []
    for i in range(0, n_conductive_divs):
        if i in range(0, n_conductive_materials):
            material_name = list(formulation.conductive_additives.keys())[i].name
            conductive_dropdown_values.append(material_name)
        else:
            conductive_dropdown_values.append(None)

    dropdown_values_response = (active_dropdown_values + binder_dropdown_values + conductive_dropdown_values)


    ## create weight fraction response
    ## create dropdown value response 
    active_weight_fractions = []
    for i in range(0, n_active_divs):
        if i in range(0, n_active_materials):
            weight_fraction = list(formulation.active_materials.values())[i]
            active_weight_fractions.append(weight_fraction)
        else:
            active_weight_fractions.append(None)

    binder_weight_fractions = []
    for i in range(0, n_binder_divs):
        if i in range(0, n_binder_materials):
            weight_fraction = list(formulation.binders.values())[i]
            binder_weight_fractions.append(weight_fraction)
        else:
            binder_weight_fractions.append(None)

    conductive_weight_fractions = []
    for i in range(0, n_conductive_divs):
        if i in range(0, n_conductive_materials):
            weight_fraction = list(formulation.conductive_additives.values())[i]
            conductive_weight_fractions.append(weight_fraction)
        else:
            conductive_weight_fractions.append(None)

    weight_fractions_response = (active_weight_fractions + binder_weight_fractions + conductive_weight_fractions)


    ## create the slider config responses
    # active_materials_slider_responses
    active_slider_config_responses = []
    material_config = get_material_config(formulation_config, 'active_material')
    for i in range(0, n_active_divs):
        if i in range(0, n_active_materials):
            material = list(formulation.active_materials.keys())[i]
            response = handle_cell_store_update(material, material_config, existing_warnings)[2:]
            active_slider_config_responses.append(response)
        else:
            none_response = tuple([[None for _ in range(0, len(material_config.parameter_list))] for _ in range(6)])
            active_slider_config_responses.append(none_response)

    flattened_active_slider_config_responses = [list(chain.from_iterable(group)) for group in zip(*active_slider_config_responses)]

    # binder slider responses
    binder_slider_config_responses = []
    material_config = get_material_config(formulation_config, 'binder')
    for i in range(0, n_binder_divs):  # Remove the duplicate inner loop
        if i in range(0, n_binder_materials):
            material = list(formulation.binders.keys())[i]
            response = handle_cell_store_update(material, material_config, existing_warnings)[2:]
            binder_slider_config_responses.append(response)
        else:
            none_response = tuple([[None for _ in range(0, len(material_config.parameter_list))] for _ in range(6)])
            binder_slider_config_responses.append(none_response)

    flattened_binder_slider_config_responses = [list(chain.from_iterable(group)) for group in zip(*binder_slider_config_responses)]

    # conductive slider responses
    conductive_slider_config_responses = []
    material_config = get_material_config(formulation_config, 'conductive_additive')
    for i in range(0, n_conductive_divs):
        if i in range(0, n_conductive_materials):
            material = list(formulation.conductive_additives.keys())[i]
            response = handle_cell_store_update(material, material_config, existing_warnings)[2:]
            conductive_slider_config_responses.append(response)
        else:
            none_response = tuple([[None for _ in range(0, len(material_config.parameter_list))] for _ in range(6)])
            conductive_slider_config_responses.append(none_response)

    flattened_conductive_slider_config_responses = [list(chain.from_iterable(group)) for group in zip(*conductive_slider_config_responses)]

    print('========')
    print("active material responses:")
    for i in flattened_active_slider_config_responses:
        print(i)
        print('----')

    print('========')
    print("binder material responses:")
    for i in flattened_binder_slider_config_responses:
        print(i)
        print('----')

    print('========')
    print("conductive material responses:")
    for i in flattened_conductive_slider_config_responses:
        print(i)
        print('----')

    flattened_config_response = tuple([ra + rb + rc for ra, rb, rc in zip(flattened_active_slider_config_responses, flattened_binder_slider_config_responses, flattened_conductive_slider_config_responses)])

    print('========')
    print("combined material responses:")
    for i in flattened_config_response:
        print(i)
        print('----')

    return (
        no_update, 
        no_update, 
        div_style_response, 
        dropdown_options_response, 
        dropdown_values_response, 
        weight_fractions_response
    ) + flattened_config_response


def handle_material_button_update(
    existing_warnings,
    trigger_id,
    formulation_config,
    active_children,
    binder_children,
    conductive_children,
    cathode_active_options: List[str] = None,
    anode_active_options: List[str] = None
):
    """Handle add/remove material button clicks with simplified approach"""
    
    action_category = trigger_id.get('action')
    material_category = trigger_id.get('material')
    
    # Define material category mappings
    category_mappings = {
        'active_material': (0, active_children),
        'binder': (1, binder_children),
        'conductive_additive': (2, conductive_children)
    }
    
    update_index, children_list = category_mappings[material_category]
    material_config = get_material_config(formulation_config, material_category)
    
    # Handle add action
    if action_category == 'add':

        new_component = create_material_component(
            material_config,
            formulation_config,
            len(children_list),
            cathode_active_options=cathode_active_options,
            anode_active_options=anode_active_options
        )

        new_children = children_list + [new_component()]
        
    # Handle remove action
    elif action_category == 'remove':
        # Don't allow removing the last active material
        if material_category == 'active_material' and len(children_list) <= 1:
            return (no_update, no_update, no_update, no_update, no_update)
        
        new_children = children_list[:-1]
        
    else:
        return (no_update, no_update, no_update, no_update, no_update)
    
    # Build response tuple with updated children at correct position
    response = [no_update, no_update, no_update, no_update, no_update]
    response[update_index + 2] = new_children  # +2 to skip warnings and store updates
    
    return tuple(response)
    
