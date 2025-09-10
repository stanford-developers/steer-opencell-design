from typing import List, Dict, Any, Tuple, NamedTuple
from dash import no_update
from itertools import chain
from copy import deepcopy

from App.formulations.configs import FormulationConfig
from App.general.handlers import _build_basic_response, handle_cell_store_update
from App.general.callback_helpers import generate_parameters, create_no_update_response, create_success_message, create_error_message
from App.general.cell_operations import set_object_to_cell, set_cell_to_cache
from App.database_service import BINDER_MATERIALS, CONDUCTIVE_ADDITIVE_MATERIALS
from App.materials.configs import MaterialType, MATERIAL_CONFIGS, MaterialConfig

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


def get_material_parameter_count(material_tag: str, formulation_config: FormulationConfig) -> int:
    """Get the number of parameters for a material type from its config"""
    material_config = get_material_config(formulation_config, material_tag)
    return len(material_config.parameter_list)


class MaterialCategoryData(NamedTuple):
    """Data structure for material category processing"""
    category_name: str
    div_styles: List[Dict[str, Any]]
    formulation_materials: Dict[Any, float]
    available_options: List[str]


class MaterialResponses(NamedTuple):
    """Data structure for material response collections"""
    styles: List[Dict[str, Any]]
    dropdown_options: List[Any]
    dropdown_values: List[Any]
    weight_fractions: List[Any]
    slider_responses: List[Tuple]


def _get_material_categories(
        
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    active_div_styles: List[Dict[str, Any]], 
    binder_div_styles: List[Dict[str, Any]], 
    conductive_div_styles: List[Dict[str, Any]],
    cathode_active_options: List[str],
    anode_active_options: List[str]

) -> List[MaterialCategoryData]:
    """Get material category data in a structured format"""
    
    active_options = cathode_active_options if formulation_config.formulation_type == CathodeFormulation else anode_active_options
    
    return [
        MaterialCategoryData(
            category_name='active_material',
            div_styles=active_div_styles,
            formulation_materials=formulation.active_materials,
            available_options=active_options
        ),
        MaterialCategoryData(
            category_name='binder',
            div_styles=binder_div_styles,
            formulation_materials=formulation.binders,
            available_options=BINDER_MATERIALS
        ),
        MaterialCategoryData(
            category_name='conductive_additive',
            div_styles=conductive_div_styles,
            formulation_materials=formulation.conductive_additives,
            available_options=CONDUCTIVE_ADDITIVE_MATERIALS
        )
    ]


def _process_material_category_styles(category_data: MaterialCategoryData) -> List[Dict[str, Any]]:
    """Process div styles for a single material category"""

    styles = category_data.div_styles.copy()
    n_materials = len(category_data.formulation_materials)
    n_divs = len(category_data.div_styles)
    
    # Explicitly set all div visibility states
    for i in range(n_divs):
        if i < n_materials:
            styles[i]['display'] = 'block'  # Show divs with materials
        else:
            styles[i]['display'] = 'none'   # Hide unused divs
    
    return styles


def _process_material_category_dropdown_options(category_data: MaterialCategoryData) -> List[Any]:
    """Process dropdown options for a single material category"""
    n_divs = len(category_data.div_styles)
    n_materials = len(category_data.formulation_materials)
    
    return [
        category_data.available_options if i < n_materials else no_update
        for i in range(n_divs)
    ]


def _process_material_category_dropdown_values(category_data: MaterialCategoryData) -> List[Any]:
    """Process dropdown values for a single material category"""
    n_divs = len(category_data.div_styles)
    n_materials = len(category_data.formulation_materials)
    material_names = [material.name for material in category_data.formulation_materials.keys()]
    
    return [
        material_names[i] if i < n_materials else None
        for i in range(n_divs)
    ]


def _process_material_category_weight_fractions(category_data: MaterialCategoryData) -> List[Any]:
    """Process weight fractions for a single material category"""
    n_divs = len(category_data.div_styles)
    n_materials = len(category_data.formulation_materials)
    weight_fractions = list(category_data.formulation_materials.values())
    
    return [
        weight_fractions[i] if i < n_materials else None
        for i in range(n_divs)
    ]


def _process_material_category_slider_responses(
    category_data: MaterialCategoryData, 
    formulation_config: FormulationConfig,
    existing_warnings: List[str]
) -> List[Tuple]:
    """Process slider responses for a single material category"""
    n_divs = len(category_data.div_styles)
    n_materials = len(category_data.formulation_materials)
    materials = list(category_data.formulation_materials.keys())
    
    material_config = get_material_config(formulation_config, category_data.category_name)
    slider_responses = []
    
    for i in range(n_divs):
        if i < n_materials:
            material = materials[i]
            response = handle_cell_store_update(material, material_config, existing_warnings)[2:]
            slider_responses.append(response)
        else:
            none_response = tuple([
                [None for _ in range(len(material_config.parameter_list))] 
                for _ in range(6)
            ])
            slider_responses.append(none_response)
    
    return slider_responses


def _process_single_material_category(
        
    category_data: MaterialCategoryData,
    formulation_config: FormulationConfig,
    existing_warnings: List[str],
    action: str = None,

) -> MaterialResponses:
    
    """Process all response types for a single material category"""

    return MaterialResponses(
        styles=_process_material_category_styles(category_data),
        dropdown_options=_process_material_category_dropdown_options(category_data),
        dropdown_values=_process_material_category_dropdown_values(category_data),
        weight_fractions=_process_material_category_weight_fractions(category_data),
        slider_responses=_process_material_category_slider_responses(category_data, formulation_config, existing_warnings)
    )


def _flatten_slider_responses(all_slider_responses: List[List[Tuple]]) -> Tuple[List, ...]:
    """Flatten slider responses from all material categories"""
    if not any(all_slider_responses):
        return tuple([] for _ in range(6))
    
    # Flatten using itertools.chain for better performance
    flattened_responses = []
    for category_responses in all_slider_responses:
        if category_responses:  # Only process if there are responses
            category_flattened = [
                list(chain.from_iterable(group)) 
                for group in zip(*category_responses)
            ]
            flattened_responses.append(category_flattened)
        else:
            # Create empty responses for this category
            flattened_responses.append([[] for _ in range(6)])
    
    # Combine all categories for each slider type (value, min, max, marks, step, input_step)  
    if not flattened_responses:
        return tuple([] for _ in range(6))
        
    return tuple([
        ra + rb + rc 
        for ra, rb, rc in zip(*flattened_responses)
    ])


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
    """
    Create MaterialSelector components based on formulation structure.
    
    This function processes formulation data and returns all necessary UI component
    values for the cathode/anode formulation interface, including div styles, 
    dropdown options/values, weight fractions, and slider configurations.
    
    Args:
        existing_warnings: List of existing warnings
        formulation: The electrode formulation object
        formulation_config: Configuration for the formulation type
        active_div_styles: Styles for active material divs
        binder_div_styles: Styles for binder divs  
        conductive_div_styles: Styles for conductive additive divs
        cathode_active_options: Available cathode active materials
        anode_active_options: Available anode active materials
        
    Returns:
        Tuple containing (warnings, cell_store, div_styles, dropdown_options, 
        dropdown_values, weight_fractions, *slider_responses)
    """
    # Get structured material category data
    material_categories = _get_material_categories(
        formulation, formulation_config, active_div_styles, binder_div_styles, 
        conductive_div_styles, cathode_active_options, anode_active_options
    )

    # Process each material category
    category_responses = [_process_single_material_category(category, formulation_config, existing_warnings) for category in material_categories]
    
    # Combine responses across all categories
    div_style_response = []
    dropdown_options_response = []
    dropdown_values_response = []
    weight_fractions_response = []
    all_slider_responses = []
    
    for response in category_responses:
        div_style_response.extend(response.styles)
        dropdown_options_response.extend(response.dropdown_options)
        dropdown_values_response.extend(response.dropdown_values)
        weight_fractions_response.extend(response.weight_fractions)
        all_slider_responses.append(response.slider_responses)
    
    # Flatten slider responses
    flattened_slider_responses = _flatten_slider_responses(all_slider_responses)
    
    # message_div
    if formulation_config.formulation_type == CathodeFormulation:
        message = create_success_message('Cathode formulation updated successfully')
    elif formulation_config.formulation_type == AnodeFormulation:
        message = create_success_message('Anode formulation updated successfully')

    return (
        message,
        no_update, 
        no_update, 
        div_style_response, 
        dropdown_options_response, 
        dropdown_values_response, 
        weight_fractions_response
    ) + flattened_slider_responses


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
    cell: Any,
    trigger_id: dict | str,
    existing_warnings: List[str],
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    active_dropdown_values: List[str],
    binder_dropdown_values: List[str],
    conductive_dropdown_values: List[str]
):
    """Handle updates triggered by indexed dropdown changes"""

    from App.formulations.callback_helpers import update_formulation_material_at_index

    # Get values from the triggered ID
    triggered_index = int(trigger_id['index'])
    triggered_category = trigger_id['material']

    # get new material
    if triggered_category == 'active_material':
        material_name = active_dropdown_values[triggered_index]
        new_material = CathodeMaterial.from_database(material_name) if formulation_config.formulation_type == CathodeFormulation else AnodeMaterial.from_database(material_name)
    elif triggered_category == 'binder':
        material_name = binder_dropdown_values[triggered_index]
        new_material = Binder.from_database(material_name)
    elif triggered_category == 'conductive_additive':
        material_name = conductive_dropdown_values[triggered_index]
        new_material = ConductiveAdditive.from_database(material_name)

    # get a new formulation with the updated material
    new_formulation = update_formulation_material_at_index(formulation, triggered_category, triggered_index, new_material)





def _modify_div_styles_for_button_action(
        
    action_category: str,
    material_category: str,
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]]

) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Modify div styles based on button action (add/remove)"""
    
    # Create copies to avoid modifying original state
    modified_active_styles = [style.copy() for style in active_div_styles]
    modified_binder_styles = [style.copy() for style in binder_div_styles]
    modified_conductive_styles = [style.copy() for style in conductive_div_styles]

    # Get current counts
    active_count = sum(1 for style in modified_active_styles if style.get('display') == 'block')
    binder_count = sum(1 for style in modified_binder_styles if style.get('display') == 'block')
    conductive_count = sum(1 for style in modified_conductive_styles if style.get('display') == 'block')

    # Handle add action
    if action_category == 'add':
        if material_category == 'active_material' and active_count < len(modified_active_styles):
            modified_active_styles[active_count]['display'] = 'block'
        elif material_category == 'binder' and binder_count < len(modified_binder_styles):
            modified_binder_styles[binder_count]['display'] = 'block'
        elif material_category == 'conductive_additive' and conductive_count < len(modified_conductive_styles):
            modified_conductive_styles[conductive_count]['display'] = 'block'

    # Handle remove action
    elif action_category == 'remove':
        if material_category == 'active_material' and active_count > 1:
            modified_active_styles[active_count - 1]['display'] = 'none'
        elif material_category == 'binder' and binder_count > 0:
            modified_binder_styles[binder_count - 1]['display'] = 'none'
        elif material_category == 'conductive_additive' and conductive_count > 0:
            modified_conductive_styles[conductive_count - 1]['display'] = 'none'

    return modified_active_styles, modified_binder_styles, modified_conductive_styles


def _clear_dropdown_values_for_hidden_divs(
        
    modified_active_styles: List[Dict[str, Any]],
    modified_binder_styles: List[Dict[str, Any]],
    modified_conductive_styles: List[Dict[str, Any]],
    active_dropdown_values: List[str],
    binder_dropdown_values: List[str],
    conductive_dropdown_values: List[str]

) -> Tuple[List[str], List[str], List[str]]:
    
    """Clear dropdown values for hidden divs"""
    
    modified_active_dropdown_values = active_dropdown_values.copy()
    modified_binder_dropdown_values = binder_dropdown_values.copy()
    modified_conductive_dropdown_values = conductive_dropdown_values.copy()

    # Clear dropdown values for hidden divs
    for i, style in enumerate(modified_active_styles):
        if style.get('display') == 'none' and i < len(modified_active_dropdown_values):
            if modified_active_dropdown_values[i] is not None:
                modified_active_dropdown_values[i] = None

    for i, style in enumerate(modified_binder_styles):
        if style.get('display') == 'none' and i < len(modified_binder_dropdown_values):
            if modified_binder_dropdown_values[i] is not None:
                modified_binder_dropdown_values[i] = None

    for i, style in enumerate(modified_conductive_styles):
        if style.get('display') == 'none' and i < len(modified_conductive_dropdown_values):
            if modified_conductive_dropdown_values[i] is not None:
                modified_conductive_dropdown_values[i] = None

    return modified_active_dropdown_values, modified_binder_dropdown_values, modified_conductive_dropdown_values


def _rebuild_formulation_materials(
        
    formulation_config: FormulationConfig,
    modified_active_dropdown_values: List[str],
    modified_binder_dropdown_values: List[str], 
    modified_conductive_dropdown_values: List[str],
    modified_active_styles: List[Dict[str, Any]],
    modified_binder_styles: List[Dict[str, Any]],
    modified_conductive_styles: List[Dict[str, Any]],
    original_formulation: CathodeFormulation | AnodeFormulation

) -> Tuple[Dict[Any, float], Dict[Any, float], Dict[Any, float]]:
    """Rebuild formulation material dictionaries based on visible dropdowns"""
    
    new_active_materials = {}
    new_binders = {}
    new_conductive_additives = {}

    # Rebuild active materials
    for i, (dropdown_value, style) in enumerate(zip(modified_active_dropdown_values, modified_active_styles)):
        if style.get('display') == 'block' and dropdown_value:
            if formulation_config.formulation_type == CathodeFormulation:
                material = CathodeMaterial.from_database(dropdown_value)
            else:
                material = AnodeMaterial.from_database(dropdown_value)
            # Use existing weight fraction or default
            weight_fraction = list(original_formulation.active_materials.values())[i] if i < len(original_formulation.active_materials) else 0.9
            new_active_materials[material] = weight_fraction

    # Rebuild binders
    for i, (dropdown_value, style) in enumerate(zip(modified_binder_dropdown_values, modified_binder_styles)):
        if style.get('display') == 'block' and dropdown_value:
            material = Binder.from_database(dropdown_value)
            weight_fraction = list(original_formulation.binders.values())[i] if i < len(original_formulation.binders) else 0.05
            new_binders[material] = weight_fraction

    # Rebuild conductive additives
    for i, (dropdown_value, style) in enumerate(zip(modified_conductive_dropdown_values, modified_conductive_styles)):
        if style.get('display') == 'block' and dropdown_value:
            material = ConductiveAdditive.from_database(dropdown_value)
            weight_fraction = list(original_formulation.conductive_additives.values())[i] if i < len(original_formulation.conductive_additives) else 0.05
            new_conductive_additives[material] = weight_fraction

    return new_active_materials, new_binders, new_conductive_additives


def _create_error_response_for_button_update(
        
    error_message: str,
    modified_active_styles: List[Dict[str, Any]],
    modified_binder_styles: List[Dict[str, Any]],
    modified_conductive_styles: List[Dict[str, Any]],
    modified_active_dropdown_values: List[str],
    modified_binder_dropdown_values: List[str],
    modified_conductive_dropdown_values: List[str],
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
    formulation_config: FormulationConfig
    
) -> Tuple:
    """Create error response that applies visual changes but prevents data corruption"""
    
    # Combine modified styles and dropdown values
    modified_styles_response = []
    modified_styles_response.extend(modified_active_styles)
    modified_styles_response.extend(modified_binder_styles) 
    modified_styles_response.extend(modified_conductive_styles)
    
    modified_dropdown_values_response = []
    modified_dropdown_values_response.extend(modified_active_dropdown_values)
    modified_dropdown_values_response.extend(modified_binder_dropdown_values)
    modified_dropdown_values_response.extend(modified_conductive_dropdown_values)
    
    # Calculate totals using config-based parameter counts
    total_divs = len(active_div_styles) + len(binder_div_styles) + len(conductive_div_styles)
    active_param_count = get_material_parameter_count('active_material', formulation_config)
    binder_param_count = get_material_parameter_count('binder', formulation_config)
    conductive_param_count = get_material_parameter_count('conductive_additive', formulation_config)
    
    total_active_sliders = len(active_div_styles) * active_param_count
    total_binder_sliders = len(binder_div_styles) * binder_param_count
    total_conductive_sliders = len(conductive_div_styles) * conductive_param_count
    total_sliders = total_active_sliders + total_binder_sliders + total_conductive_sliders
    
    # Create default slider responses for hidden divs
    default_slider_values = []
    for i, style in enumerate(modified_active_styles):
        default_slider_values.extend([None] * active_param_count if style.get('display') == 'none' else [no_update] * active_param_count)
    for i, style in enumerate(modified_binder_styles):
        default_slider_values.extend([None] * binder_param_count if style.get('display') == 'none' else [no_update] * binder_param_count)
    for i, style in enumerate(modified_conductive_styles):
        default_slider_values.extend([None] * conductive_param_count if style.get('display') == 'none' else [no_update] * conductive_param_count)
    
    slider_responses = (
        default_slider_values,
        [no_update] * total_sliders,
        [no_update] * total_sliders,
        [no_update] * total_sliders,
        [no_update] * total_sliders,
        [no_update] * total_sliders
    )
    
    return (
        error_message,
        no_update,
        no_update,
        modified_styles_response,
        [no_update] * total_divs,
        modified_dropdown_values_response,
        [no_update] * total_divs
    ) + slider_responses


def _create_success_response_for_button_update(
        
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    cell,
    modified_active_styles: List[Dict[str, Any]],
    modified_binder_styles: List[Dict[str, Any]],
    modified_conductive_styles: List[Dict[str, Any]],
    modified_active_dropdown_values: List[str],
    modified_binder_dropdown_values: List[str],
    modified_conductive_dropdown_values: List[str],
    cathode_active_options: List[str],
    anode_active_options: List[str],
    existing_warnings: List[str],
    action_category: str

) -> Tuple:
    """Create success response with updated cell and properly formatted outputs"""
    
    # Update cell with modified formulation
    new_cell = set_object_to_cell(cell, formulation, formulation_config)
    new_key = set_cell_to_cache(new_cell)

    # Get structured material category data using modified styles
    material_categories = _get_material_categories(
        formulation, formulation_config, modified_active_styles, modified_binder_styles,
        modified_conductive_styles, cathode_active_options, anode_active_options
    )

    # Process responses using existing helper functions
    div_style_response = []
    dropdown_options_response = []
    dropdown_values_response = []
    weight_fractions_response = []
    all_slider_responses = []
    
    for i, category in enumerate(material_categories):
        div_style_response.extend(category.div_styles)
        dropdown_options_response.extend(_process_material_category_dropdown_options(category))
        
        # Use modified dropdown values for remove actions
        if action_category == 'remove' and i == 0:
            padded_values = modified_active_dropdown_values + [None] * (len(category.div_styles) - len(modified_active_dropdown_values))
            dropdown_values_response.extend(padded_values[:len(category.div_styles)])
        elif action_category == 'remove' and i == 1:
            padded_values = modified_binder_dropdown_values + [None] * (len(category.div_styles) - len(modified_binder_dropdown_values))
            dropdown_values_response.extend(padded_values[:len(category.div_styles)])
        elif action_category == 'remove' and i == 2:
            padded_values = modified_conductive_dropdown_values + [None] * (len(category.div_styles) - len(modified_conductive_dropdown_values))
            dropdown_values_response.extend(padded_values[:len(category.div_styles)])
        else:
            dropdown_values_response.extend(_process_material_category_dropdown_values(category))
            
        weight_fractions_response.extend(_process_material_category_weight_fractions(category))
        slider_responses = _process_material_category_slider_responses(category, formulation_config, existing_warnings)
        all_slider_responses.append(slider_responses)
    
    flattened_slider_responses = _flatten_slider_responses(all_slider_responses)
    message = create_success_message('Cathode formulation updated successfully')

    return (
        message,
        no_update,
        {'cache_key': new_key},
        div_style_response,
        dropdown_options_response,
        dropdown_values_response,
        weight_fractions_response
    ) + flattened_slider_responses


def handle_material_button_update(
    cell,
    trigger_id: Dict[str, str | float],
    existing_warnings: Dict[str, str | float],
    formulation: CathodeFormulation | AnodeFormulation,
    formulation_config: FormulationConfig,
    active_div_styles: List[Dict[str, Any]],
    binder_div_styles: List[Dict[str, Any]],
    conductive_div_styles: List[Dict[str, Any]],
    active_dropdown_values: List[str],
    binder_dropdown_values: List[str],
    conductive_dropdown_values: List[str],
    cathode_active_options: List[Dict[str, Any]],
    anode_active_options: List[Dict[str, Any]]
):
    """Handle add/remove material button clicks with clean, modular approach"""
    
    action_category = trigger_id.get('action')
    material_category = trigger_id.get('material')

    # Step 1: Modify div styles based on button action
    modified_active_styles, modified_binder_styles, modified_conductive_styles = _modify_div_styles_for_button_action(
        action_category, material_category, active_div_styles, binder_div_styles, conductive_div_styles
    )

    # Step 2: Clear dropdown values for hidden divs
    modified_active_dropdown_values, modified_binder_dropdown_values, modified_conductive_dropdown_values = _clear_dropdown_values_for_hidden_divs(
        modified_active_styles, modified_binder_styles, modified_conductive_styles,
        active_dropdown_values, binder_dropdown_values, conductive_dropdown_values
    )

    # Step 3: Try to recreate formulation with remaining materials
    if action_category == 'remove':
        try:
            new_active_materials, new_binders, new_conductive_additives = _rebuild_formulation_materials(
                formulation_config, modified_active_dropdown_values, modified_binder_dropdown_values,
                modified_conductive_dropdown_values, modified_active_styles, modified_binder_styles,
                modified_conductive_styles, formulation
            )

            # Update formulation with new materials
            formulation.active_materials = new_active_materials
            formulation.binders = new_binders
            formulation.conductive_additives = new_conductive_additives

            # Test formulation creation - raises exception if invalid
            test_formulation = formulation_config.formulation_type(
                active_materials=formulation.active_materials,
                binders=formulation.binders,
                conductive_additives=formulation.conductive_additives
            )

        except Exception as e:
            # Step 4a: Return error response (visual changes applied, no data corruption)
            error_message = create_error_message(f'Failed to update formulation: {str(e)}')
            return _create_error_response_for_button_update(
                error_message, modified_active_styles, modified_binder_styles, modified_conductive_styles,
                modified_active_dropdown_values, modified_binder_dropdown_values, modified_conductive_dropdown_values,
                active_div_styles, binder_div_styles, conductive_div_styles, formulation_config
            )

    # Step 4b: Return success response
    return _create_success_response_for_button_update(
        formulation, formulation_config, cell, modified_active_styles, modified_binder_styles,
        modified_conductive_styles, modified_active_dropdown_values, modified_binder_dropdown_values,
        modified_conductive_dropdown_values, cathode_active_options, anode_active_options,
        existing_warnings, action_category
    )

