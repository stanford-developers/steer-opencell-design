from typing import List, Dict, Any, Tuple
from dash import no_update

from App.formulations.configs import FormulationConfig, FORMULATION_CONFIGS
from App.general.handlers import _build_basic_response
from App.materials.configs import MaterialType, MATERIAL_CONFIGS, MaterialConfig
from App.general.callback_helpers import generate_parameters, create_no_update_response
from App.general.enumerated_classes import FormulationType

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation
from steer_materials.CellMaterials.Electrode import CathodeMaterial, AnodeMaterial, Binder, ConductiveAdditive
from steer_core.Apps.Utils.SliderControls import create_slider_config


# Simple category to material type mapping
CATEGORY_TO_MATERIAL_TYPE = {
    'binder': MaterialType.BINDER,
    'conductive_additive': MaterialType.CONDUCTIVE_ADDITIVE,
}

# Formulation type to active material type mapping  
FORMULATION_TO_ACTIVE_MATERIAL = {
    CathodeFormulation: MaterialType.CATHODE_ACTIVE_MATERIAL,
    AnodeFormulation: MaterialType.ANODE_ACTIVE_MATERIAL,
}


def get_material_config(formulation_config: FormulationConfig, category_name: str) -> MaterialConfig:
    """Get the appropriate material config based on formulation and category"""
    if category_name == 'active_material':
        material_type = FORMULATION_TO_ACTIVE_MATERIAL[formulation_config.formulation_type]
    else:
        material_type = CATEGORY_TO_MATERIAL_TYPE[category_name]
    
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
    
    return (existing_warnings, no_update) + tuple(responses)


def handle_cell_store_update_material_children(
        existing_warnings: List[float], 
        formulation: CathodeFormulation | AnodeFormulation, 
        formulation_config: FormulationConfig
) -> Tuple[Any, Any, List[Any], List[Any], List[Any]]:
    """Create MaterialSelector components based on formulation structure"""
    from App.formulations.callback_helpers import create_material_component
    
    try:
        # Get material configs for each category
        active_config = get_material_config(formulation_config, 'active_material')
        binder_config = get_material_config(formulation_config, 'binder')
        conductive_config = get_material_config(formulation_config, 'conductive_additive')
        
        # Define material data configurations
        material_data_configs = [
            (formulation.active_materials, active_config),
            (formulation.binders, binder_config),
            (formulation.conductive_additives, conductive_config),
        ]
        
        # Create children for each material category
        children_lists = [
            _create_material_children_list(materials, config, formulation_config)
            for materials, config in material_data_configs
        ]
        
        active_children, binder_children, conductive_children = children_lists
        
        return (no_update, no_update, active_children, binder_children, conductive_children)
        
    except Exception as e:
        print(f"Error creating material components: {e}")
        return no_update, no_update, [], [], []


def _create_material_children_list(
    materials: Dict[Any, float], 
    material_config: Any, 
    formulation_config: FormulationConfig
) -> List[Any]:
    """
    Create a list of MaterialSelector components from materials dictionary.
    
    Args:
        materials: Dictionary mapping material objects to weight percentages
        material_config: Configuration object for the material type
        formulation_config: Formulation configuration object
        
    Returns:
        List of MaterialSelector component instances
    """
    if not materials:
        return []
    
    from App.formulations.callback_helpers import create_material_component
    
    children = []
    for i, (material, weight_percent) in enumerate(materials.items()):
        component = create_material_component(
            material_config=material_config,
            formulation_config=formulation_config,
            index=i,
            material=material,
            weight_percent=weight_percent,
            empty=False
        )
        children.append(component())
    
    return children


def handle_material_button_update(
    existing_warnings,
    trigger_id,
    formulation_config,
    active_children,
    binder_children,
    conductive_children
):
    """Handle add/remove material button clicks with simplified approach"""
    from App.formulations.callback_helpers import create_material_component
    
    action_category = trigger_id.get('action')
    material_category = trigger_id.get('material')
    
    # Define material category mappings
    category_mappings = {
        'active_material': ('active_material', active_children),
        'binder': ('binder', binder_children),
        'conductive_additive': ('conductive_additive', conductive_children)
    }
    
    if material_category not in category_mappings:
        return no_update, no_update, active_children, binder_children, conductive_children
    
    try:
        category_name, children_list = category_mappings[material_category]
        material_config = get_material_config(formulation_config, category_name)
        
        # Handle add/remove actions
        if action_category == 'add':
            new_index = len(children_list)
            new_component = create_material_component(material_config, formulation_config, new_index)
            children_list.append(new_component())
            
        elif action_category == 'remove':
            # Only remove if there are children and it's not the last active material
            if material_category == 'active_material':
                if children_list and len(children_list) > 1:
                    children_list.pop()
            else:
                if children_list:
                    children_list.pop()
        
        return no_update, no_update, active_children, binder_children, conductive_children
        
    except Exception as e:
        print(f"Error handling material button update: {e}")
        return no_update, no_update, active_children, binder_children, conductive_children

