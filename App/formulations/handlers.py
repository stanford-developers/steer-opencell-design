from App.materials.configs import MaterialType, MATERIAL_CONFIGS
from App.general.callback_helpers import create_trigger_data

from steer_opencell_design.Formulations.ElectrodeFormulations import CathodeFormulation, AnodeFormulation

from dash import no_update


def handle_indexed_dropdown_update(
        existing_warnings,
        trigger_id,
        cell,
        formulation,
        formulation_config,
        dropdown_values
):
    pass


def handle_cell_store_update_material_children(existing_warnings, formulation):

    """Create empty MaterialSelector components based on formulation structure."""
    
    from App.formulations.callback_helpers import create_empty_material_component

    # Determine the active material type based on the formulation
    if isinstance(formulation, CathodeFormulation):
        active_material_config = MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL]
    elif isinstance(formulation, AnodeFormulation):
        active_material_config = MATERIAL_CONFIGS[MaterialType.ANODE_ACTIVE_MATERIAL]
    else:
        raise ValueError("Unsupported formulation type for material children creation.")

    # Get the binder and conductive additive configs
    binder_config = MATERIAL_CONFIGS[MaterialType.BINDER]
    conductive_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]

    def create_children_list(material_dictionary, material_config):
        """Create a list of empty MaterialSelector components."""
        children = []
        for i in range(len(material_dictionary)):
            empty_component = create_empty_material_component(material_config, i)
            children.append(empty_component())
        return children

    # Create empty components based on the number of active materials in the formulation
    active_material_children = create_children_list(formulation.active_materials, active_material_config)

    # Create empty components based on the number of binder materials in the formulation
    binder_children = create_children_list(formulation.binders, binder_config)

    # Create empty components based on the number of conductive materials in the formulation
    conductive_children = create_children_list(formulation.conductive_additives, conductive_config)

    # create a store object holding trigger data
    trigger_data = create_trigger_data()

    return no_update, no_update, active_material_children, binder_children, conductive_children, trigger_data


def handle_material_button_update(
    existing_warnings,
    triggered_id,
    config,
    active_children,
    binder_children,
    conductive_children
):
    """Handle add/remove material button clicks."""
    
    from App.formulations.callback_helpers import create_empty_material_component

    action_category = triggered_id.get('action')
    material_category = triggered_id.get('material')

    # Get the the material config from the triggered id
    if material_category == 'CathodeActiveMaterial':
        material_config = MATERIAL_CONFIGS[MaterialType.CATHODE_ACTIVE_MATERIAL]
    elif material_category == 'AnodeActiveMaterial':
        material_config = MATERIAL_CONFIGS[MaterialType.ANODE_ACTIVE_MATERIAL]
    elif material_category == 'Binder':
        material_config = MATERIAL_CONFIGS[MaterialType.BINDER]
    elif material_category == 'ConductiveAdditive':
        material_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]

    # Handle the case that a material is being added
    if action_category == 'add':
        if material_category == 'CathodeActiveMaterial' or material_category == 'AnodeActiveMaterial':
            new_index = len(active_children)
            new_component = create_empty_material_component(material_config, new_index)
            active_children.append(new_component())
        elif material_category == 'Binder':
            new_index = len(binder_children)
            new_component = create_empty_material_component(material_config, new_index)
            binder_children.append(new_component())
        elif material_category == 'ConductiveAdditive':
            new_index = len(conductive_children)
            new_component = create_empty_material_component(material_config, new_index)
            conductive_children.append(new_component())

    # Handle the case that a material is being removed
    elif action_category == 'remove':
        if material_category == 'CathodeActiveMaterial' or material_category == 'AnodeActiveMaterial':
            if active_children and len(active_children) > 1:
                active_children.pop()
        elif material_category == 'Binder':
            if binder_children:
                binder_children.pop()
        elif material_category == 'ConductiveAdditive':
            if conductive_children:
                conductive_children.pop()

    # create a store object holding trigger data
    trigger_data = create_trigger_data()

    # Return updated children lists
    return no_update, no_update, active_children, binder_children, conductive_children, trigger_data



def handle_cell_store_update_material_values(
    formulation,
    config,
    existing_warnings
):
    """Handle cell store updates - populate all material component values from the formulation."""
    
    from App.general.callback_helpers import generate_parameters
    from steer_core.Apps.Utils.SliderControls import create_slider_config
    
    # Initialize output lists
    dropdown_values = []
    all_parameter_values = []
    all_min_values = []
    all_max_values = []
    
    # Helper function to process a single material
    def process_material(material, material_config):
        """Process a single material and add its parameters to the output lists."""
        # Add dropdown value (material name)
        dropdown_values.append(material.name)
        
        # Generate parameters for this material
        parameter_values, min_values, max_values = generate_parameters(material, material_config)
        
        # Add to combined lists
        all_parameter_values.extend(parameter_values)
        all_min_values.extend(min_values)
        all_max_values.extend(max_values)
    
    # Process active materials
    for active_material, weight_percent in formulation.active_materials.items():
        active_material_config = MATERIAL_CONFIGS[MaterialType.ACTIVE_MATERIAL]
        process_material(active_material, active_material_config)
    
    # Process binders
    for binder, weight_percent in formulation.binders.items():
        binder_config = MATERIAL_CONFIGS[MaterialType.BINDER]
        process_material(binder, binder_config)
    
    # Process conductive additives
    for conductive_additive, weight_percent in formulation.conductive_additives.items():
        conductive_additive_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]
        process_material(conductive_additive, conductive_additive_config)
    
    # Create slider configurations for all parameters at once
    if all_parameter_values:
        slider_configs = create_slider_config(all_min_values, all_max_values, all_parameter_values)
        
        slider_values = slider_configs['grid_slider_vals']
        slider_mins = slider_configs['min_vals']
        slider_maxs = slider_configs['max_vals']
        slider_marks = slider_configs['mark_vals']
        slider_steps = slider_configs['step_vals']
        input_steps = slider_configs['input_step_vals']
    else:
        # Handle empty case
        slider_values = []
        slider_mins = []
        slider_maxs = []
        slider_marks = []
        slider_steps = []
        input_steps = []
    
    return (
        existing_warnings,  # warnings_store
        no_update,          # cell_store (no update for cell store changes)
        dropdown_values,    # dropdown values
        slider_values,      # slider values
        slider_mins,        # slider mins
        slider_maxs,        # slider maxs
        slider_marks,       # slider marks
        slider_steps,       # slider steps
        input_steps         # input steps (removed input_values)
    )


def handle_material_selector_dropdown_update(
    existing_warnings,
    triggered_id,
    cell,
    formulation,
    config,
    dropdown_values
):
    """Handle dropdown changes - update material and refresh slider/input values."""
    
    # Parse the triggered ID to get material info
    material_type = triggered_id['material']
    index = triggered_id['index']
    
    # Get the new material name from dropdown values
    if not dropdown_values or index >= len(dropdown_values):
        return (
            existing_warnings,  # warnings_store
            no_update,          # cell_store 
            no_update,          # dropdown values (no_update for ALL pattern when no change needed)
            no_update,          # slider values (no_update for ALL pattern when no change needed)
            no_update,          # slider mins (no_update for ALL pattern when no change needed)
            no_update,          # slider maxs (no_update for ALL pattern when no change needed)
            no_update,          # slider marks (no_update for ALL pattern when no change needed)
            no_update,          # slider steps (no_update for ALL pattern when no change needed)
            no_update           # input steps (no_update for ALL pattern when no change needed)
        )
    
    new_material_name = dropdown_values[index]
    if not new_material_name:
        return (
            existing_warnings,  # warnings_store
            no_update,          # cell_store 
            no_update,          # dropdown values (no_update for ALL pattern when no change needed)
            no_update,          # slider values (no_update for ALL pattern when no change needed)
            no_update,          # slider mins (no_update for ALL pattern when no change needed)
            no_update,          # slider maxs (no_update for ALL pattern when no change needed)
            no_update,          # slider marks (no_update for ALL pattern when no change needed)
            no_update,          # slider steps (no_update for ALL pattern when no change needed)
            no_update           # input steps (no_update for ALL pattern when no change needed)
        )
    
    # Get the appropriate material from database
    if material_type == 'active_material':
        # Get from active materials store or database
        new_material = get_active_material_from_database(new_material_name)
        material_config = MATERIAL_CONFIGS[MaterialType.ACTIVE_MATERIAL]
        # Update formulation
        formulation.update_active_material(index, new_material, weight_percent=10.0)  # Default weight
        
    elif material_type == 'binder':
        new_material = get_binder_from_database(new_material_name)
        material_config = MATERIAL_CONFIGS[MaterialType.BINDER]
        formulation.update_binder(index, new_material, weight_percent=5.0)  # Default weight
        
    elif material_type == 'conductive_additive':
        new_material = get_conductive_additive_from_database(new_material_name)
        material_config = MATERIAL_CONFIGS[MaterialType.CONDUCTIVE_ADDITIVE]
        formulation.update_conductive_additive(index, new_material, weight_percent=2.0)  # Default weight
    
    # Update cell in cache
    from App.cache_service import cache
    cache.set(cell.cache_key, cell)
    
    # Return updated cell and call cell store update handler to refresh all values
    return handle_cell_store_update_material_values(formulation, config, existing_warnings)


def handle_material_property_update(
    existing_warnings,
    triggered_id,
    cell,
    formulation,
    config,
    input_values,
    slider_values
):
    """Handle property changes in material sliders/inputs."""
    
    # This follows the same pattern as other property updates
    from App.general.handlers import handle_property_update
    
    return handle_property_update(
        existing_warnings,
        triggered_id,
        cell,
        formulation,
        config,
        input_values,
        slider_values,
    )


# Helper functions for database access
def get_active_material_from_database(material_name):
    """Get active material from database by name."""
    # This should be implemented based on your database structure
    from App.database_service import get_material_by_name
    return get_material_by_name(material_name, 'active_material')


def get_binder_from_database(material_name):
    """Get binder from database by name."""
    from steer_materials.CellMaterials.Electrode import Binder
    return Binder.from_database(material_name)


def get_conductive_additive_from_database(material_name):
    """Get conductive additive from database by name."""
    from steer_materials.CellMaterials.Electrode import ConductiveAdditive
    return ConductiveAdditive.from_database(material_name)

